# -*- coding: utf-8 -*-
"""Kardeş sunucu adayları.

Bazı yayıncılar aynı yayını iki ayrı adresten verir (TRT: medya ↔ live,
Turkuvaz: turknet.ercdn ↔ trkvz-live.ercdn). Listede bir adres görülünce kardeşi
de aday yapılır; sağlık testinden geçerse kanala yedek kaynak olur. Ana adres
düşerse oynatıcı hazır yedeğe geçer.

Kurallar config.SIBLING_RULES'ta: (desen, şablon).
"""
import re

from . import config as C
from .parse import Channel

_RULES = [(re.compile(p, re.I), t) for p, t in C.SIBLING_RULES]


def sibling_urls(url):
    """Bir adresin bilinen kardeş adresleri (kendisi hariç)."""
    out = []
    u = (url or "").strip()
    for rx, tpl in _RULES:
        m = rx.match(u)
        if m:
            alt = m.expand(tpl)
            if alt != u and alt not in out:
                out.append(alt)
    return out


def expand(pool, have):
    """pool'daki kanallar için kardeş adaylar üretir. have: zaten bilinen adresler (güncellenir)."""
    extra = []
    for c in pool:
        for alt in sibling_urls(c.url):
            if alt in have:
                continue
            have.add(alt)
            n = Channel(name=c.name, url=alt, logo=c.logo, group=c.group, tvg_id=c.tvg_id,
                        headers=dict(c.headers or {}), source=c.source or "sibling")
            n.raw_name = getattr(c, "raw_name", c.name)
            n.src_group = getattr(c, "src_group", c.group)
            extra.append(n)
    return extra
