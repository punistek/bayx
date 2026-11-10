"""Selçuk: giriş sayfası -> gerçek sayfa -> player JS -> HLS adayları."""
import re
from .common import absolute, active_home, hls_url, item, pick, try_get

CHANNELS = {
    'selcukobs1': 'beIN Sports 1', 'selcukbeinsports2': 'beIN Sports 2',
    'selcukbeinsports3': 'beIN Sports 3', 'selcukbeinsports4': 'beIN Sports 4',
    'selcukbeinsports5': 'beIN Sports 5', 'selcukssport': 'S Sport 1',
    'selcukssport2': 'S Sport 2', 'selcuksmartspor': 'Smart Spor 1',
    'selcuktivibuspor1': 'Tivibu Spor 1', 'selcuktivibuspor2': 'Tivibu Spor 2',
    'selcuktivibuspor3': 'Tivibu Spor 3', 'selcuktivibuspor4': 'Tivibu Spor 4',
    'selcuktabiispor1': 'Tabii Spor 1', 'selcuktabiispor2': 'Tabii Spor 2',
    'selcuktabiispor3': 'Tabii Spor 3', 'selcuktabiispor4': 'Tabii Spor 4',
    'selcuktabiispor5': 'Tabii Spor 5',
}


def discover(client, conf):
    page = active_home(client, conf)
    if not page:
        return []
    landing = page
    # Giriş sayfasındaki dinamik alan adı (varsa)
    domain = pick([r'href=["\'](https?://[^"\']*selcuksportshd[^"\']+)["\']'], page.text)
    if domain:
        candidate = try_get(client, domain)
        if candidate:
            landing = candidate
    players = re.findall(r'(?:data-url|href)=["\']([^"\']+(?:index\.php|player)[^"\']*\bid=[^"\']+)["\']',
                         landing.text, re.I)
    base = pick([r'(?:this\.)?baseStreamUrl\s*[:=]\s*["\']([^"\']+)["\']',
                 r'\bstreamUrl\s*=\s*["\']([^"\']+)["\']'], landing.text)
    for path in players[:10]:
        if base:
            break
        p = try_get(client, absolute(landing.url, path), {'Referer': landing.url})
        if p:
            base = pick([r'(?:this\.)?baseStreamUrl\s*[:=]\s*["\']([^"\']+)["\']',
                         r'\bstreamUrl\s*=\s*["\']([^"\']+)["\']'], p.text)
    if not base:
        return []
    base = absolute(landing.url, base)
    if not base:
        return []
    root = base.split('/live/')[0] + '/live/' if '/live/' in base else base.rstrip('/') + '/live/'
    out = []
    for cid, name in (conf.get('channels') or CHANNELS).items():
        stream = hls_url(root + cid + '/playlist.m3u8', root)
        ch = item('selcuk', name, stream, referer=landing.url)
        if ch: out.append(ch)
    return out
