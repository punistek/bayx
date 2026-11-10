"""MahsunSports / Andro: event.html içindeki baseurls listesini kullanır."""
import re
from .common import absolute, active_home, item, origin_of, pick, safe_url, try_get

CHANNELS = {
    'androstreamlivebs1':'beIN Sports 1', 'androstreamlivebs2':'beIN Sports 2',
    'androstreamlivebs3':'beIN Sports 3', 'androstreamlivebs4':'beIN Sports 4',
    'androstreamlivebs5':'beIN Sports 5', 'androstreamlivebsm1':'beIN Sports Max 1',
    'androstreamlivebsm2':'beIN Sports Max 2', 'androstreamlivess1':'S Sport 1',
    'androstreamlivess2':'S Sport 2', 'androstreamlivets1':'Tivibu Spor 1',
    'androstreamlivets2':'Tivibu Spor 2', 'androstreamlivets3':'Tivibu Spor 3',
    'androstreamlivets4':'Tivibu Spor 4', 'androstreamlivesm1':'Smart Spor 1',
    'androstreamlivees1':'Eurosport 1', 'androstreamlivees2':'Eurosport 2',
}


def discover(client, conf):
    home = active_home(client, conf)
    if not home:
        return []
    domain = origin_of(home.url)
    page = try_get(client, absolute(domain, conf.get('event_path', '/event.html?id=androstreamlivebs1')),
                   {'Referer': domain + '/'})
    if not page:
        return []
    raw = pick([r'\bbaseurls\s*=\s*\[([^\]]+)\]'], page.text)
    if not raw:
        return []
    servers = [s.strip() for s in re.findall(r'["\'](https?://[^"\']+)["\']', raw) if safe_url(s)]
    out = []
    for server in dict.fromkeys(servers[:8]):
        root = server.rstrip('/')
        path = '' if '/checklist' in root else '/checklist'
        for cid, name in (conf.get('channels') or CHANNELS).items():
            ch = item('andro', name, root + path + '/' + cid + '.m3u8', referer=domain + '/')
            if ch: out.append(ch)
    return out
