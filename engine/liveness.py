# -*- coding: utf-8 -*-
"""
Canlılık testi — işin kalbi. Bir yayının GERÇEKTEN aktığını doğrular:
  1. Linke oynatıcı gibi istek atar.
  2. HLS (.m3u8) ise manifesti okur, içindeki gerçek video parçasına (.ts) iner,
     o parçadan birkaç yüz bayt gerçek veri gelip gelmediğine bakar.
  3. Doğrudan akış (.ts vb.) ise ilk baytların gerçek video olup olmadığına bakar.
HTML hata sayfaları, "expired/forbidden/403", boş cevaplar = ÖLÜ.
"""
import re
from urllib.parse import urljoin

from . import config as C
from .fetch import PLAYER

ERROR_WORDS = ("expired", "invalid", "unauthorized", "bad token", "denied",
               "forbidden", "403", "404", "not found", "error", "<html", "<!doctype")
DEAD_CT = ("text/html", "application/json", "text/plain")


def _looks_binary(chunk):
    if not chunk or len(chunk) < C.SEGMENT_MINBYTES:
        return False
    low = chunk[:600].decode("utf-8", "ignore").lower()
    return not any(w in low for w in ERROR_WORDS)


def _fetch_head(url, timeout):
    """(status, content_type, ilk_metin, ham_chunk) döndür ya da None."""
    try:
        with PLAYER.get(url, timeout=timeout, stream=True, allow_redirects=True,
                        headers={"Range": "bytes=0-4095"}) as r:
            ct = r.headers.get("Content-Type", "").lower()
            chunk = r.raw.read(4096)
            return r.status_code, ct, chunk.decode("utf-8", "ignore"), chunk
    except Exception:
        return None


def _test_once(url, timeout):
    head = _fetch_head(url, timeout)
    if not head:
        return False
    status, ct, text, chunk = head
    if status not in (200, 206):
        return False
    low = text.lower()

    # HLS manifesti mi?
    if "#extm3u" in low or "#extinf" in low or "#ext-x" in low:
        # manifest içinden ilk gerçek satırı (alt manifest ya da .ts parçası) bul
        target = None
        for ln in text.splitlines():
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            target = ln if ln.lower().startswith("http") else urljoin(url, ln)
            break
        if not target:
            return False
        # alt manifest ise bir kademe daha in
        sub = _fetch_head(target, timeout)
        if not sub:
            return False
        s2, ct2, t2, chunk2 = sub
        if s2 not in (200, 206):
            return False
        if "#extm3u" in t2.lower() or "#ext-x" in t2.lower():
            seg = None
            for ln in t2.splitlines():
                ln = ln.strip()
                if ln and not ln.startswith("#"):
                    seg = ln if ln.lower().startswith("http") else urljoin(target, ln)
                    break
            if not seg:
                return False
            final = _fetch_head(seg, timeout)
            return bool(final and final[0] in (200, 206) and _looks_binary(final[3]))
        # doğrudan parça geldiyse
        return _looks_binary(chunk2)

    # Doğrudan akış (.ts, mp4, mpegts) — içerik türü ve baytlara bak
    if any(t in ct for t in ("video/", "mpegurl", "octet-stream", "mp2t", "mpeg")):
        return _looks_binary(chunk) or status == 206
    if any(t in ct for t in DEAD_CT):
        return False
    # içerik türü belirsizse baytlara güven
    return _looks_binary(chunk)


def is_alive(url, timeout=None):
    timeout = timeout or C.TEST_TIMEOUT
    if not re.match(r"https?://", url or "", re.I):
        return False
    for _ in range(C.TEST_RETRY + 1):
        if _test_once(url, timeout):
            return True
    return False
