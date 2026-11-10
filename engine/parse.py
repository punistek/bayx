# -*- coding: utf-8 -*-
"""M3U metnini kanal nesnelerine çevirir ve kanalları tekrar M3U'ya yazar."""
import re

ATTR_RE = re.compile(r'([\w-]+)="([^"]*)"')


class Channel:
    __slots__ = ("name", "url", "logo", "group", "tvg_id", "extra", "source", "alive")

    def __init__(self, name, url, logo="", group="", tvg_id="", extra=None, source=""):
        self.name = name
        self.url = url
        self.logo = logo
        self.group = group or ""
        self.tvg_id = tvg_id
        self.extra = extra or []      # #EXTVLCOPT / #KODIPROP gibi satırlar
        self.source = source          # hangi kaynaktan geldi
        self.alive = None             # True / False / None (test edilmedi)

    def to_m3u(self):
        attrs = f'tvg-id="{self.tvg_id}" tvg-logo="{self.logo}" group-title="{self.group}"'
        out = [f"#EXTINF:-1 {attrs},{self.name}"]
        out.extend(self.extra)
        out.append(self.url)
        return "\n".join(out)


def parse(text, source=""):
    """M3U metnini Channel listesine çevir."""
    chans, cur = [], None
    for raw in (text or "").splitlines():
        line = raw.strip().lstrip("﻿")
        if not line:
            continue
        up = line.upper()
        if up.startswith("#EXTINF"):
            head, _, name = line.partition(",")
            attrs = dict(ATTR_RE.findall(head))
            cur = Channel(
                name=(name.strip() or attrs.get("tvg-name", "") or "Adsız"),
                url="", logo=attrs.get("tvg-logo", ""),
                group=attrs.get("group-title", ""), tvg_id=attrs.get("tvg-id", ""),
                source=source)
        elif up.startswith("#EXTGRP:") and cur:
            cur.group = line.split(":", 1)[1].strip() or cur.group
        elif up.startswith(("#EXTVLCOPT", "#KODIPROP", "#EXTHTTP")) and cur:
            cur.extra.append(line)
        elif line.startswith("#"):
            continue
        else:
            if cur is None:
                cur = Channel(name=line.rsplit("/", 1)[-1][:60], url="", source=source)
            cur.url = line
            if cur.url:
                chans.append(cur)
            cur = None
    return chans


def write_m3u(channels):
    out = ["#EXTM3U"]
    for c in channels:
        out.append(c.to_m3u())
    return "\n".join(out) + "\n"
