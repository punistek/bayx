# -*- coding: utf-8 -*-
"""Resmî kaynak çözücü: kanalın KENDİ canlı yayın sayfasından güncel adres.

Büyük kanalların yayın adresleri (ör. daioncdn ?app=... anahtarı) zaman zaman
değişir; kopya listeler eski adresle kalır. Bu katman her turda kanalın kendi
sayfasını okur, sayfada herkese açık duran yayın adresini kalıpla bulur ve aday
yapar. Aday diğerleri gibi sağlık testinden geçer.

Tanımlar official_sources.json'da (depo kökünde), elle düzenlenebilir:
  {"name": "Show TV", "page": "https://www.showtv.com.tr/canli-yayin",
   "pattern": "https://ciner\\.daioncdn\\.net/showtv/[^\"'<>\\s]+",
   "headers": {"Referer": "https://www.showtv.com.tr/"}}
  - pattern'da grup varsa 1. grup, yoksa eşleşmenin tamamı alınır.
  - "json_path": sayfa JSON ise (ör. "VideoUrl") o alanın değeri alınır.
Yalnızca sayfada herkese açık verilen adresler okunur; oturum, DRM ya da erişim
kontrolü aşılmaz.
"""
import html
import json
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor

from . import config as C
from .fetch import get_text
from .parse import Channel

log = logging.getLogger("official")

# Adresin devamı: tırnak/boşluk/<> ve tek başına ters eğik çizgi bitirir; "\/" devam eder.
TAIL = r"""(?:\\/|[^"'\s<>\\])*"""
DEFAULT_PATTERN = r"""https?:(?:\\?/){2}(?:\\/|[^"'\s<>\\])+?\.m3u8""" + TAIL


def load_defs(path=None):
    path = path or C.OFFICIAL_FILE
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:  # bozuk dosya motoru durdurmasın
        log.warning("official_sources.json okunamadı: %s", e)
        return []
    items = data.get("channels", data) if isinstance(data, dict) else data
    return [d for d in items if isinstance(d, dict) and d.get("name") and d.get("page")
            and d.get("enabled", True)]


def _clean(u):
    u = u.replace("\\/", "/").replace("\\u0026", "&").replace("\\u002F", "/")
    return html.unescape(u).strip().strip("\"'")


def _pattern(d):
    """Tanımın kalıbı. "host" (+ "path") verilmişse kalıp ondan kurulur; JSON içinde
    kaçışlı yazılmış adresleri (ters eğik çizgili) de yakalar."""
    if d.get("pattern"):
        return d["pattern"]
    host = d.get("host")
    if host:
        path = (d.get("path") or "").strip("/")
        sep = r"(?:\\?/)+"
        p = r"https?:" + sep + re.escape(host)
        if path:
            p += sep + sep.join(re.escape(x) for x in path.split("/"))
        return p + TAIL
    return DEFAULT_PATTERN


def extract(text, d):
    """Sayfa metninden yayın adresini çıkarır; yoksa None."""
    if not text:
        return None
    jp = d.get("json_path")
    if jp:
        m = re.search(r'"' + re.escape(jp) + r'"\s*:\s*"([^"]+)"', text)
        return _clean(m.group(1)) if m else None
    m = re.search(_pattern(d), text)
    if not m:
        return None
    u = m.group(1) if m.groups() and m.group(1) else m.group(0)
    u = _clean(u)
    if u.startswith("//"):
        u = "https:" + u
    return u if u.lower().startswith(("http://", "https://")) else None


def resolve_one(d):
    hdrs = dict(d.get("page_headers") or {})
    text = get_text(d["page"], timeout=C.HTTP_TIMEOUT, headers=hdrs or None,
                    max_bytes=3_000_000)
    url = extract(text, d)
    if not url:
        log.info("Resmî sayfada adres bulunamadı: %s (%s)", d["name"], d["page"])
        return None
    c = Channel(name=d["name"], url=url, logo=d.get("logo", ""), group=d.get("group", ""),
                tvg_id=d.get("tvg_id", ""), headers=dict(d.get("headers") or {}),
                source="official:" + d["page"])
    c.raw_name = d["name"]
    return c


def collect(defs=None):
    defs = load_defs() if defs is None else defs
    if not defs:
        return []
    with ThreadPoolExecutor(max_workers=min(8, len(defs))) as ex:
        found = [c for c in ex.map(resolve_one, defs) if c]
    log.info("Resmî sayfalardan %d/%d kanal adresi çözüldü", len(found), len(defs))
    return found
