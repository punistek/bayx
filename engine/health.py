# -*- coding: utf-8 -*-
"""
Motorun hafızası: her yayın adresinin ve her kaynak listesinin test geçmişi.

state/urls.json     adres → geçmiş testler, puan, karantina, kanal bilgisi
state/sources.json  kaynak m3u → indirme başarısı, verdiği canlı kanal sayısı, karantina

Puan (0-100):
  güvenilirlik  45  (yakın testler daha ağır basan başarı oranı)
  şu anki durum 20  (ok 20, kararsız 8, ölü/engelli 0)
  açılış hızı   15  (≤800 ms tam puan, 5 sn'de sıfır)
  kalite        10  (1080p 10, 720p 8, 576p 5, bilinmiyor 4, düşük 3)
  akış          10  (ilerlemesi doğrulandı 10, bilinmiyor 5, donuk 0)
  ceza: sertifika bozuk −25, yalnızca ses −30
"""
import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone

from . import config as C

log = logging.getLogger("health")


def now_ts():
    return int(time.time())


def iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if ts else None


def url_key(url):
    return hashlib.sha1(url.strip().encode("utf-8")).hexdigest()[:16]


def _load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def atomic_write(path, text):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def dump_json(path, obj, compact=False):
    if compact:
        txt = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    else:
        txt = json.dumps(obj, ensure_ascii=False, indent=1)
    atomic_write(path, txt + "\n")


# ============================================================ adres hafızası
class UrlState:
    def __init__(self, path=None):
        self.path = path or C.URL_STATE
        self.data = _load(self.path).get("urls", {})

    def get(self, url):
        return self.data.get(url_key(url))

    def ensure(self, ch):
        k = url_key(ch.url)
        rec = self.data.get(k)
        if rec is None:
            rec = self.data[k] = {"url": ch.url, "first_seen": now_ts(), "runs": [],
                                  "fails_row": 0, "last_ok": 0, "q_until": 0}
        # kanal bilgisini güncel tut (kaynak listesi kaybolsa bile kanal yeniden kurulabilsin)
        rec.update({"name": ch.name, "cid": ch.cid, "group": ch.group, "logo": ch.logo,
                    "tvg_id": ch.tvg_id, "headers": ch.headers, "source": ch.source,
                    "armored": bool(ch.armored), "seen": now_ts()})
        return rec

    def quarantined(self, url, t=None):
        rec = self.get(url)
        return bool(rec and rec.get("q_until", 0) > (t or now_ts()))

    def record(self, ch, p):
        rec = self.ensure(ch)
        t = now_ts()
        rec["runs"] = (rec.get("runs", []) + [{
            "t": t, "s": p.status, "r": C.REGION, "ms": p.latency_ms,
        }])[-C.HISTORY_LEN:]
        if p.ok:
            rec["fails_row"] = 0
            rec["last_ok"] = t
            rec.setdefault("last_ok_region", {})[C.REGION] = t
            rec["q_until"] = 0
        elif p.status == "blocked":
            rec["fails_row"] = rec.get("fails_row", 0) + 0.5       # engel ≠ ölüm
        else:
            rec["fails_row"] = rec.get("fails_row", 0) + 1
        if rec["fails_row"] >= C.QUARANTINE_AFTER and not ch.armored:
            n = int(rec["fails_row"] - C.QUARANTINE_AFTER)
            hours = min(C.QUARANTINE_BASE_H * (2 ** n), C.QUARANTINE_MAX_H)
            rec["q_until"] = t + int(hours * 3600)
        for k in ("width", "height", "codecs", "vcodec", "kind", "tls_insecure", "encrypted",
                  "has_video", "has_audio", "progress"):
            v = getattr(p, k)
            if v not in (None, "", 0) or k in ("tls_insecure", "progress"):
                rec[k] = v
        rec["status"], rec["reason"], rec["latency_ms"] = p.status, p.reason, p.latency_ms
        rec["score"] = score(rec, p)
        return rec

    def recent_good(self, days=None, include_blocked=False):
        """Son X günde sağlam olan adresler (kaynak listesi geçici yoksa bile tekrar test için).
        include_blocked: bölge engelli olanlar da (Türkiye doğrulaması için)."""
        lim = now_ts() - int((days or C.REMEMBER_OK_DAYS) * 86400)
        return [r for r in self.data.values() if r.get("last_ok", 0) >= lim
                or (include_blocked and r.get("status") == "blocked")]

    def prune(self, live_urls):
        """Uzun süredir ölü ve hiçbir kaynakta artık görünmeyen adresleri unut."""
        drop = [k for k, r in self.data.items()
                if r.get("fails_row", 0) >= C.FORGET_AFTER_FAILS and not r.get("armored")
                and r.get("url") not in live_urls]
        for k in drop:
            del self.data[k]
        return len(drop)

    def save(self):
        dump_json(self.path, {"updated": iso(now_ts()), "count": len(self.data),
                              "urls": self.data}, compact=True)


def reliability(runs):
    """Yakın testler daha ağır basan başarı oranı (0..1)."""
    if not runs:
        return 0.5
    w_sum = s_sum = 0.0
    for i, r in enumerate(reversed(runs)):
        w = 0.85 ** i
        w_sum += w
        s_sum += w * (1.0 if r["s"] == "ok" else 0.6 if r["s"] == "unstable"
                      else 0.3 if r["s"] == "blocked" else 0.0)
    return s_sum / w_sum


def score(rec, p):
    s = 45 * reliability(rec.get("runs"))
    s += {"ok": 20, "unstable": 8}.get(p.status, 0)
    ms = p.latency_ms or 0
    if p.ok:
        s += 15 if ms <= 800 else max(0.0, 15 * (5000 - ms) / 4200)
    h = p.height or rec.get("height") or 0
    s += 10 if h >= 1000 else 8 if h >= 700 else 5 if h >= 540 else 3 if h else 4
    prog = p.progress
    s += 10 if prog is True else 0 if prog is False else 5
    if p.tls_insecure:
        s -= C.TLS_PENALTY
    if p.has_video is False and p.ok:
        s -= 30
    if not p.ok:
        s = min(s, 30)
    return max(0, min(100, int(round(s))))


def geo_grace(rec):
    """GitHub'dan engelli ama başka bölgede (ör. Türkiye) yakın zamanda sağlam mı?"""
    lim = now_ts() - C.GEO_GRACE_HOURS * 3600
    regions = rec.get("last_ok_region", {})
    return any(r != C.REGION and t >= lim for r, t in regions.items())


# ============================================================ kaynak hafızası
class SourceState:
    def __init__(self, path=None):
        self.path = path or C.SOURCE_STATE
        self.data = _load(self.path).get("sources", {})

    def rec(self, url):
        return self.data.setdefault(url, {"runs": 0, "fetch_ok": 0, "fails_row": 0,
                                          "zero_row": 0, "q_until": 0, "found": 0,
                                          "alive": 0, "alive_hist": [], "kind": "auto"})

    def quarantined(self, url):
        r = self.data.get(url)
        return bool(r and r.get("q_until", 0) > now_ts())

    def fetched(self, url, ok, found, kind):
        r = self.rec(url)
        r["runs"] += 1
        r["kind"] = kind
        r["last_run"] = now_ts()
        if ok:
            r["fetch_ok"] += 1
            r["fails_row"] = 0
            r["found"] = found
        else:
            r["fails_row"] += 1

    def yielded(self, url, alive):
        r = self.rec(url)
        r["alive"] = alive
        r["alive_hist"] = (r.get("alive_hist", []) + [alive])[-10:]
        r["zero_row"] = 0 if alive else r.get("zero_row", 0) + 1
        if r["kind"] == "auto" and (r["zero_row"] >= C.SOURCE_ZERO_YIELD_LIMIT or r["fails_row"] >= 4):
            r["q_until"] = now_ts() + C.SOURCE_QUARANTINE_H * 3600

    def quality(self, url):
        """Kaynağın verimliliği (test önceliği için)."""
        r = self.data.get(url)
        if not r or not r.get("alive_hist"):
            return 0.5
        h = r["alive_hist"]
        return min(1.0, sum(h) / len(h) / 20.0) + 0.1

    def save(self):
        dump_json(self.path, {"updated": iso(now_ts()), "sources": self.data})
