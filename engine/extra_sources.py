# -*- coding: utf-8 -*-
"""m3u biçiminde OLMAYAN açık kanal veritabanları.

famelack-data: ülke başına sıkıştırılmış (gzip) JSON. Her kanalda ad, logo ve
sources.streams listesi var. Adaylar diğerleri gibi süzgeç + sağlık testinden geçer.
"""
import gzip
import json
import logging

from . import config as C
from .fetch import make_session
from .parse import Channel

log = logging.getLogger("extra")


def famelack(url=None):
    url = url or C.FAMELACK_TR
    if not url:
        return []
    try:
        r = make_session().get(url, timeout=C.HTTP_TIMEOUT)
        if r.status_code != 200:
            return []
        raw = r.content
        try:
            raw = gzip.decompress(raw)
        except OSError:
            pass  # zaten düz JSON
        data = json.loads(raw.decode("utf-8", "ignore"))
    except Exception as e:
        log.info("famelack okunamadı: %s", e)
        return []
    out = []
    for ch in data if isinstance(data, list) else []:
        if not isinstance(ch, dict):
            continue
        name = (ch.get("name") or "").strip()
        if not name:
            continue
        streams = ((ch.get("sources") or {}).get("streams") or []) if isinstance(ch.get("sources"), dict) else []
        for s in streams:
            if isinstance(s, str) and s.lower().startswith(("http://", "https://")):
                c = Channel(name=name, url=s.strip(), logo=ch.get("logo") or "", source=url)
                out.append(c)
    log.info("famelack: %d aday", len(out))
    return out
