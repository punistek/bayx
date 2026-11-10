# -*- coding: utf-8 -*-
"""
M3U metnini kanal nesnelerine çevirir ve kanalları tekrar M3U'ya yazar.

ÖNEMLİ: Yayın başlıklarını (User-Agent / Referer / Origin) kaynak listedeki her
biçimden çıkarır:
  - #EXTVLCOPT:http-user-agent= / http-referrer= / http-origin=
  - #EXTHTTP:{"User-Agent":"...","Referer":"...","Origin":"..."}
  - #KODIPROP:inputstream.adaptive.stream_headers=User-Agent=...&Referer=...
  - URL sonundaki  |User-Agent=...&Referer=...&Origin=...  eki
Sonra çıktı listesine (tr.m3u) bunları TEMİZ #EXTVLCOPT satırları olarak yazar,
böylece oynatıcı (ve bizim uygulama) yayını doğru başlıklarla açar.
"""
import json
import re

ATTR_RE = re.compile(r'([\w-]+)="([^"]*)"')


class Channel:
    __slots__ = ("name", "url", "logo", "group", "tvg_id", "extra", "headers",
                 "source", "alive", "cid", "armored", "raw_name", "src_group")

    def __init__(self, name, url, logo="", group="", tvg_id="", extra=None,
                 headers=None, source=""):
        self.name = name
        self.url = url
        self.logo = logo
        self.group = group or ""
        self.tvg_id = tvg_id
        self.extra = extra or []        # başlık OLMAYAN ek satırlar (DRM vb.)
        self.headers = headers or {}    # User-Agent / Referer / Origin ...
        self.source = source
        self.alive = None
        self.cid = ""            # kanal kimliği (identity.py)
        self.armored = False     # zirhli.m3u'dan mı geldi
        self.raw_name = name     # kaynaktaki orijinal ad
        self.src_group = self.group   # kaynaktaki orijinal grup adı

    def to_m3u(self, name=None, url=None, headers=None, extra_attrs=None):
        attrs = (f'tvg-id="{_q(self.tvg_id)}" tvg-name="{_q(name or self.name)}" '
                 f'tvg-logo="{_q(self.logo)}" group-title="{_q(self.group)}"')
        if extra_attrs:
            for k, v in extra_attrs.items():
                attrs += f' {k}="{_q(v)}"'
        out = [f"#EXTINF:-1 {attrs},{name or self.name}"]
        hdr = self.headers if headers is None else headers
        # Başlıkları temiz EXTVLCOPT olarak yaz (her oynatıcı okur)
        ua = _get(hdr, "user-agent")
        ref = _get(hdr, "referer") or _get(hdr, "referrer")
        org = _get(hdr, "origin")
        if ua:
            out.append(f"#EXTVLCOPT:http-user-agent={ua}")
        if ref:
            out.append(f"#EXTVLCOPT:http-referrer={ref}")
        if org:
            out.append(f"#EXTVLCOPT:http-origin={org}")
        # Başlık dışındaki diğer özel satırlar (varsa) aynen
        for e in self.extra:
            out.append(e)
        out.append(url or self.url)
        return "\n".join(out)


def _q(v):
    return (v or "").replace('"', "'")


def _split_extinf(line):
    """#EXTINF satırını (öznitelikler, ad) diye böl. Tırnak içindeki virgülü atla:
    #EXTINF:-1 tvg-name="TV 8,5" group-title="X",TV 8,5  →  ad = 'TV 8,5'"""
    inq = False
    for i, ch in enumerate(line):
        if ch == '"':
            inq = not inq
        elif ch == "," and not inq:
            return line[:i], line[i + 1:]
    return line, ""


def _get(d, key):
    for k, v in d.items():
        if k.lower() == key:
            return v
    return None


def _add_header(hdrs, k, v):
    k = (k or "").strip()
    v = (v or "").strip()
    if not k or not v:
        return
    lk = k.lower()
    if lk in ("user-agent", "useragent"):
        hdrs["User-Agent"] = v
    elif lk in ("referer", "referrer"):
        hdrs["Referer"] = v
    elif lk == "origin":
        hdrs["Origin"] = v
    else:
        hdrs[k] = v


def _parse_header_blob(hdrs, blob):
    # "User-Agent=..&Referer=.." ya da "User-Agent: ..|Referer: .."
    for part in re.split(r"[&|]", blob):
        m = re.search(r"[=:]", part)
        if m:
            _add_header(hdrs, part[:m.start()], part[m.start() + 1:])


def parse(text, source=""):
    """M3U metnini Channel listesine çevir (başlıklar dahil)."""
    chans = []
    name = logo = group = tvg_id = None
    extra = []
    headers = {}

    def reset():
        nonlocal name, logo, group, tvg_id, extra, headers
        name = logo = group = tvg_id = None
        extra = []
        headers = {}

    for raw in (text or "").splitlines():
        line = raw.strip().lstrip("﻿")
        if not line:
            continue
        up = line.upper()
        if up.startswith("#EXTINF"):
            head, nm = _split_extinf(line)
            attrs = dict(ATTR_RE.findall(head))
            name = nm.strip() or attrs.get("tvg-name", "") or "Adsız"
            logo = attrs.get("tvg-logo", "")
            group = attrs.get("group-title", "")
            tvg_id = attrs.get("tvg-id", "")
        elif up.startswith("#EXTGRP:"):
            group = line.split(":", 1)[1].strip() or group
        elif up.startswith("#EXTVLCOPT:"):
            body = line.split(":", 1)[1]
            eq = body.find("=")
            if eq > 0:
                key = body[:eq].lower()
                val = body[eq + 1:]
                if "user-agent" in key:
                    _add_header(headers, "User-Agent", val)
                elif "referrer" in key or "referer" in key:
                    _add_header(headers, "Referer", val)
                elif "origin" in key:
                    _add_header(headers, "Origin", val)
                else:
                    extra.append(line)
        elif up.startswith("#EXTHTTP:"):
            try:
                for k, v in json.loads(line.split(":", 1)[1]).items():
                    _add_header(headers, k, str(v))
            except Exception:
                pass
        elif up.startswith("#KODIPROP:"):
            body = line.split(":", 1)[1]
            low = body.lower()
            if "stream_headers" in low or "manifest_headers" in low:
                eq = body.find("=")
                if eq > 0:
                    _parse_header_blob(headers, body[eq + 1:])
            else:
                extra.append(line)  # DRM vb. korunur
        elif line.startswith("#"):
            continue
        else:
            # URL satırı: | ekindeki başlıkları çıkar, URL'yi temizle
            url = line
            pipe = url.find("|")
            if pipe > 0:
                _parse_header_blob(headers, url[pipe + 1:])
                url = url[:pipe]
            if name is None:
                name = url.rsplit("/", 1)[-1][:60]
            chans.append(Channel(
                name=name, url=url, logo=logo or "", group=group or "",
                tvg_id=tvg_id or "", extra=list(extra),
                headers=dict(headers), source=source))
            reset()
    return chans


def header_attrs(text):
    """#EXTM3U satırındaki x-tvg-url vb. öznitelikleri döndür."""
    for raw in (text or "").splitlines()[:5]:
        if raw.strip().lstrip("\ufeff").upper().startswith("#EXTM3U"):
            return dict(ATTR_RE.findall(raw))
    return {}


def write_m3u(channels):
    out = ["#EXTM3U"]
    for c in channels:
        out.append(c.to_m3u())
    return "\n".join(out) + "\n"
