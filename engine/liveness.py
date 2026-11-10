# -*- coding: utf-8 -*-
"""
Yayın sağlık testi — üç kademe:

  1) HIZLI TEST (probe)
     - Adrese oynatıcı gibi istek atılır, açılış gecikmesi ölçülür.
     - HLS: ana manifest → en iyi kalite varyantı → medya manifesti → canlı uçtaki
       gerçek segment indirilir ve İÇERİĞİ doğrulanır (MPEG-TS senkron baytları,
       fMP4 kutuları, AAC/ID3). HTML hata sayfası, boş cevap, bitmiş (VOD) yayın = ölü.
     - DASH (.mpd): manifest canlı (dynamic) mı bakılır.
     - Doğrudan akış (.ts vb.): ilk 64 KB'de geçerli MPEG-TS paketleri aranır.
     - 401/403/451 → "blocked" (bölge engeli olabilir, ölü sayılmaz).

  2) İLERLEME TESTİ (recheck)
     - HLS medya manifesti birkaç saniye sonra tekrar okunur. Medya sırası
       (EXT-X-MEDIA-SEQUENCE) veya son segment ilerlememişse yayın DONMUŞ demektir.

  3) DERİN TEST (deep_probe) — FFprobe
     - Yalnızca en iyi adaylarda. Video/ses akışı var mı, codec, çözünürlük.
"""
import json
import re
import shutil
import ssl
import subprocess
import time
from dataclasses import asdict, dataclass, field
from urllib.parse import urljoin

import requests

from . import config as C
from .fetch import PLAYER, PLAYER_INSECURE

ERROR_WORDS = ("expired", "invalid", "unauthorized", "bad token", "denied",
               "forbidden", "not found", "<html", "<!doctype", "<body", "error")
BLOCK_CODES = (401, 403, 451)
_ATTR = re.compile(r'([A-Z0-9-]+)=("[^"]*"|[^,]*)')


@dataclass
class Probe:
    url: str
    status: str = "dead"          # ok | unstable | dead | blocked
    reason: str = ""
    kind: str = ""                # hls | dash | ts | ?
    latency_ms: int = 0
    http: int = 0
    width: int = 0
    height: int = 0
    bandwidth: int = 0
    codecs: str = ""
    progress: object = None       # True / False / None (bilinmiyor)
    tls_insecure: bool = False
    encrypted: str = ""           # "", "aes-128", "drm"
    has_video: object = None      # FFprobe sonucu
    has_audio: object = None
    vcodec: str = ""
    deep: bool = False
    # ilerleme testi için iç durum
    _media_url: str = field(default="", repr=False)
    _seq: int = field(default=-1, repr=False)
    _last_seg: str = field(default="", repr=False)
    _target: float = field(default=0.0, repr=False)
    _t: float = field(default=0.0, repr=False)
    _headers: dict = field(default_factory=dict, repr=False)

    @property
    def ok(self):
        return self.status in ("ok", "unstable")

    def public(self):
        return {k: v for k, v in asdict(self).items() if not k.startswith("_")}


class _Fail(Exception):
    def __init__(self, status, reason, http=0):
        super().__init__(reason)
        self.status, self.reason, self.http = status, reason, http


# ======================================================================== HTTP
def _get(url, headers, max_bytes, timeout, insecure=False, rng=None):
    """(status, content_type, body_bytes, final_url, elapsed_ms)."""
    sess = PLAYER_INSECURE if insecure else PLAYER
    h = dict(headers or {})
    if rng:
        h["Range"] = f"bytes=0-{rng - 1}"
    t0 = time.monotonic()
    with sess.get(url, headers=h, timeout=(timeout, timeout), stream=True,
                  allow_redirects=True) as r:
        buf = bytearray()
        deadline = t0 + timeout * 1.5
        for chunk in r.iter_content(16384):
            buf.extend(chunk)
            if len(buf) >= max_bytes or time.monotonic() > deadline:
                break
        ms = int((time.monotonic() - t0) * 1000)
        return r.status_code, r.headers.get("Content-Type", "").lower(), bytes(buf), r.url, ms


def _text(b):
    return b.decode("utf-8", "ignore")


def _is_error_body(b):
    low = _text(b[:800]).lower()
    return any(w in low for w in ERROR_WORDS)


# ================================================================ içerik doğrulama
def _is_mpegts(b):
    """En az 3 ardışık 188 baytlık TS paketi (0x47 senkron) bul."""
    n = len(b)
    for off in range(0, min(188, n)):
        if b[off] == 0x47 and off + 376 < n and b[off + 188] == 0x47 and b[off + 376] == 0x47:
            return True
    return False


def _is_fmp4(b):
    head = b[:4096]
    return any(t in head for t in (b"ftyp", b"moof", b"styp", b"sidx", b"mdat"))


def _is_aac_or_id3(b):
    if b[:3] == b"ID3":
        # ID3 başlığını atla, arkasında TS veya ADTS ara
        if len(b) > 10:
            size = (b[6] << 21) | (b[7] << 14) | (b[8] << 7) | b[9]
            rest = b[10 + size:]
            return _is_mpegts(rest) or (len(rest) > 2 and rest[0] == 0xFF and rest[1] & 0xF0 == 0xF0) \
                or len(rest) >= C.SEGMENT_MINBYTES
        return False
    return len(b) > 2 and b[0] == 0xFF and (b[1] & 0xF6) == 0xF0


def media_bytes_ok(b, encrypted=False):
    if not b or len(b) < C.SEGMENT_MINBYTES:
        return False
    if encrypted:                      # şifreli segment: rastgele görünür, hata sayfası olmasın yeter
        return not _is_error_body(b)
    return _is_mpegts(b) or _is_fmp4(b) or _is_aac_or_id3(b)


# ================================================================ HLS ayrıştırma
def _attrs(s):
    return {k: v.strip('"') for k, v in _ATTR.findall(s)}


def parse_master(text, base):
    """Varyantları döndür: [{url, bw, w, h, codecs}]"""
    out, pending = [], None
    for ln in text.splitlines():
        ln = ln.strip()
        if ln.upper().startswith("#EXT-X-STREAM-INF"):
            a = _attrs(ln.split(":", 1)[1] if ":" in ln else "")
            w = h = 0
            if "RESOLUTION" in a and "x" in a["RESOLUTION"].lower():
                try:
                    w, h = (int(x) for x in a["RESOLUTION"].lower().split("x")[:2])
                except ValueError:
                    pass
            try:
                bw = int(a.get("BANDWIDTH", "0") or 0)
            except ValueError:
                bw = 0
            pending = {"bw": bw, "w": w, "h": h, "codecs": a.get("CODECS", "")}
        elif pending is not None and ln and not ln.startswith("#"):
            pending["url"] = urljoin(base, ln)
            out.append(pending)
            pending = None
    return out


def parse_media(text, base):
    seq, target, segs, ended, key = 0, 0.0, [], False, ""
    for ln in text.splitlines():
        ln = ln.strip()
        up = ln.upper()
        if up.startswith("#EXT-X-MEDIA-SEQUENCE:"):
            try:
                seq = int(ln.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif up.startswith("#EXT-X-TARGETDURATION:"):
            try:
                target = float(ln.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif up.startswith("#EXT-X-ENDLIST"):
            ended = True
        elif up.startswith("#EXT-X-KEY") and "METHOD=NONE" not in up:
            a = _attrs(ln.split(":", 1)[1])
            fmt = a.get("KEYFORMAT", "identity").lower()
            key = "aes-128" if a.get("METHOD", "").upper() == "AES-128" and fmt == "identity" else "drm"
        elif up.startswith("#EXT-X-MAP:") and not segs:
            pass
        elif ln and not ln.startswith("#"):
            segs.append(urljoin(base, ln))
    return {"seq": seq, "target": target, "segs": segs, "ended": ended, "key": key}


def _pick_variant(variants):
    """En yüksek çözünürlük (≤1080p tercih), eşitse en yüksek bant genişliği."""
    def k(v):
        h = v["h"] or 0
        return (h if h <= 1080 else 1080 - (h - 1080) / 10000, v["bw"])
    return sorted(variants, key=k, reverse=True)


# ================================================================ kademe 1
def _probe_once(url, headers, insecure):
    p = Probe(url=url, _headers=dict(headers or {}))
    t = C.TEST_TIMEOUT
    code, ct, body, final, ms = _get(url, headers, C.MANIFEST_MAX_BYTES, t, insecure)
    p.http, p.latency_ms = code, ms
    if code in BLOCK_CODES:
        raise _Fail("blocked", f"http {code}", code)
    if code not in (200, 206):
        raise _Fail("dead", f"http {code}", code)
    head = _text(body[:2048]).lstrip("﻿ \r\n\t")
    up = head[:200].upper()

    # ---------------------------------------------------------------- HLS
    if up.startswith("#EXTM3U") or "#EXT-X-" in up or "mpegurl" in ct:
        p.kind = "hls"
        text = _text(body)
        media_url, media_text = final, text
        variants = parse_master(text, final)
        if variants:
            ordered = _pick_variant(variants)
            last_err = None
            for v in ordered[:2]:                     # en iyi varyant olmazsa bir alt kalite
                try:
                    c2, _, b2, f2, _ = _get(v["url"], headers, C.MANIFEST_MAX_BYTES, t, insecure)
                except requests.RequestException as e:
                    last_err = _Fail("dead", f"variant: {type(e).__name__}")
                    continue
                if c2 in BLOCK_CODES:
                    last_err = _Fail("blocked", f"variant http {c2}", c2)
                    continue
                if c2 not in (200, 206) or "#EXT" not in _text(b2[:2048]).upper():
                    last_err = _Fail("dead", f"variant http {c2}", c2)
                    continue
                media_url, media_text = f2, _text(b2)
                p.width, p.height, p.bandwidth, p.codecs = v["w"], v["h"], v["bw"], v["codecs"]
                break
            else:
                raise last_err or _Fail("dead", "no variant")
        m = parse_media(media_text, media_url)
        if not m["segs"]:
            # bazı sunucular master içinde tekrar master döndürür
            nested = parse_master(media_text, media_url)
            if nested:
                c3, _, b3, f3, _ = _get(_pick_variant(nested)[0]["url"], headers,
                                        C.MANIFEST_MAX_BYTES, t, insecure)
                if c3 in (200, 206):
                    media_url, m = f3, parse_media(_text(b3), f3)
            if not m["segs"]:
                raise _Fail("dead", "empty playlist")
        if m["ended"] and C.VOD_IS_DEAD:
            raise _Fail("dead", "vod (endlist)")
        if m["key"] == "drm":
            p.encrypted = "drm"
            raise _Fail("dead", "drm")
        p.encrypted = m["key"]
        # canlı uca yakın segment (son segment henüz yazılıyor olabilir → sondan 2.)
        seg = m["segs"][-2] if len(m["segs"]) >= 2 else m["segs"][-1]
        c4, ct4, b4, _, _ = _get(seg, headers, C.SEGMENT_READ_BYTES, t, insecure,
                                 rng=C.SEGMENT_READ_BYTES)
        if c4 in BLOCK_CODES:
            raise _Fail("blocked", f"segment http {c4}", c4)
        if c4 not in (200, 206):
            raise _Fail("dead", f"segment http {c4}", c4)
        if not media_bytes_ok(b4, encrypted=bool(p.encrypted)):
            raise _Fail("dead", "segment not media")
        p._media_url, p._seq, p._last_seg = media_url, m["seq"], m["segs"][-1]
        p._target, p._t = m["target"] or 6.0, time.monotonic()
        p.status, p.reason = "ok", "hls segment ok"
        return p

    # ---------------------------------------------------------------- DASH
    if "<mpd" in head[:600].lower() or "dash+xml" in ct:
        p.kind = "dash"
        low = _text(body).lower()
        if 'type="static"' in low and C.VOD_IS_DEAD:
            raise _Fail("dead", "dash static (vod)")
        if "contentprotection" in low:
            p.encrypted = "drm"
            raise _Fail("dead", "drm")
        p.status, p.reason = "ok", "dash manifest ok"
        return p

    # ---------------------------------------------------------------- doğrudan akış
    p.kind = "ts" if _is_mpegts(body) else "?"
    if media_bytes_ok(body):
        p.status, p.reason = "ok", "direct media ok"
        return p
    if any(x in ct for x in ("text/html", "application/json", "text/plain")) or _is_error_body(body):
        raise _Fail("dead", f"not media ({ct or 'unknown'})")
    if len(body) < C.SEGMENT_MINBYTES:
        raise _Fail("dead", "too little data")
    raise _Fail("dead", "unknown format")


def probe(url, headers=None, retries=1):
    """Hızlı test. Her zaman bir Probe döndürür (hata fırlatmaz)."""
    if not re.match(r"https?://", url or "", re.I):
        return Probe(url=url, status="dead", reason="bad url")
    last = Probe(url=url, status="dead", reason="?")
    for attempt in range(retries + 1):
        insecure = False
        try:
            try:
                return _probe_once(url, headers, insecure=False)
            except requests.exceptions.SSLError:
                insecure = True
                p = _probe_once(url, headers, insecure=True)
                p.tls_insecure = True
                p.reason += " (tls bozuk)"
                return p
        except _Fail as f:
            last = Probe(url=url, status=f.status, reason=f.reason, http=f.http,
                         tls_insecure=insecure)
            if f.status == "blocked" or f.reason.startswith(("vod", "drm", "http 404", "http 410")):
                return last                       # tekrar denemeye değmez
        except requests.exceptions.Timeout:
            last = Probe(url=url, status="dead", reason="timeout")
        except requests.exceptions.ConnectionError as e:
            last = Probe(url=url, status="dead", reason="connect: " + _short(e))
        except (requests.RequestException, ssl.SSLError, ValueError) as e:
            last = Probe(url=url, status="dead", reason=type(e).__name__)
        except Exception as e:  # beklenmeyen: motoru durdurmasın
            last = Probe(url=url, status="dead", reason="err: " + type(e).__name__)
        if attempt < retries:
            time.sleep(0.5)
    return last


def _short(e):
    s = str(e)
    for k in ("Name or service not known", "Connection refused", "timed out",
              "Max retries", "RemoteDisconnected", "reset"):
        if k in s:
            return k
    return type(e).__name__


# ================================================================ kademe 2
def recheck(p):
    """HLS yayını ilerliyor mu? (donma testi). Probe'u yerinde günceller."""
    if p.status != "ok" or p.kind != "hls" or not p._media_url:
        return p
    wait = min(max(p._target, C.PROGRESS_MIN_WAIT), C.PROGRESS_MAX_WAIT)
    rest = wait - (time.monotonic() - p._t)
    if rest > 0:
        time.sleep(rest)
    try:
        code, _, body, final, _ = _get(p._media_url, p._headers, C.MANIFEST_MAX_BYTES,
                                       C.TEST_TIMEOUT, p.tls_insecure)
    except Exception:
        p.status, p.reason, p.progress = "unstable", "recheck failed", None
        return p
    if code not in (200, 206):
        p.status, p.reason, p.progress = "unstable", f"recheck http {code}", None
        return p
    m = parse_media(_text(body), final)
    if not m["segs"]:
        p.status, p.reason, p.progress = "unstable", "recheck empty", None
        return p
    moved = m["seq"] > p._seq or m["segs"][-1] != p._last_seg
    p.progress = moved
    if not moved:
        p.status, p.reason = "unstable", "frozen (no new segments)"
    return p


# ================================================================ kademe 3
def ffprobe_available():
    return bool(shutil.which(C.FFPROBE_BIN))


def deep_probe(p):
    """FFprobe ile video/ses akışlarını doğrula. Probe'u yerinde günceller."""
    if not p.ok or not ffprobe_available():
        return p
    hdrs = p._headers or {}
    cmd = [C.FFPROBE_BIN, "-v", "error", "-hide_banner",
           "-rw_timeout", str(int(C.TEST_TIMEOUT * 1e6)),
           "-analyzeduration", "4000000", "-probesize", "3000000",
           "-show_entries", "stream=codec_type,codec_name,width,height",
           "-of", "json"]
    ua = next((v for k, v in hdrs.items() if k.lower() == "user-agent"), None)
    cmd += ["-user_agent", ua or "ExoPlayerLib/2.19.1"]
    extra = "".join(f"{k}: {v}\r\n" for k, v in hdrs.items() if k.lower() != "user-agent")
    if extra:
        cmd += ["-headers", extra]
    if p.tls_insecure:
        cmd += ["-tls_verify", "0"]
    cmd.append(p.url)
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=C.DEEP_TIMEOUT, text=True)
        data = json.loads(r.stdout or "{}")
    except subprocess.TimeoutExpired:
        p.deep, p.reason = True, p.reason + " · ffprobe timeout"
        return p
    except (ValueError, OSError):
        return p
    streams = data.get("streams") or []
    p.deep = True
    v = next((s for s in streams if s.get("codec_type") == "video" and s.get("width")), None)
    p.has_video = v is not None
    p.has_audio = any(s.get("codec_type") == "audio" for s in streams)
    if v:
        p.vcodec = v.get("codec_name", "")
        p.width, p.height = v.get("width") or p.width, v.get("height") or p.height
    if not streams:
        p.status, p.reason = "dead", "ffprobe: no streams"
    elif not p.has_video:
        p.status, p.reason = "unstable", "audio only"
    return p
