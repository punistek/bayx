"""XSport: ana sayfadaki player URL -> this.baseStreamUrl -> HLS."""
import re
from .common import absolute, active_home, item, pick, try_get

CHANNELS = {
    'xbeinsports-1':'beIN Sports 1', 'xbeinsports-2':'beIN Sports 2',
    'xbeinsports-3':'beIN Sports 3', 'xbeinsports-4':'beIN Sports 4',
    'xbeinsports-5':'beIN Sports 5', 'xbeinsportsmax-1':'beIN Sports Max 1',
    'xbeinsportsmax-2':'beIN Sports Max 2', 'xtivibuspor-1':'Tivibu Spor 1',
    'xtivibuspor-2':'Tivibu Spor 2', 'xtivibuspor-3':'Tivibu Spor 3',
    'xtivibuspor-4':'Tivibu Spor 4', 'xssport':'S Sport 1',
    'xssport2':'S Sport 2', 'xtabiispor1':'Tabii Spor 1',
    'xtabiispor2':'Tabii Spor 2', 'xtabiispor3':'Tabii Spor 3',
    'xtabiispor4':'Tabii Spor 4', 'xtabiispor5':'Tabii Spor 5',
}


def discover(client, conf):
    home = active_home(client, conf)
    if not home:
        return []
    urls = re.findall(r'data-url=["\']([^"\']+)["\']', home.text, re.I)
    by_id = {}
    for path in urls:
        m = re.search(r'[?&]id=([\w-]+)', path, re.I)
        if m and m.group(1) not in by_id:
            by_id[m.group(1)] = absolute(home.url, path)
    result = []
    for cid, name in (conf.get('channels') or CHANNELS).items():
        player = by_id.get(cid)
        p = try_get(client, player, {'Referer': home.url}) if player else None
        if not p:
            continue
        base = pick([r'(?:this\.)?baseStreamUrl\s*[:=]\s*["\']([^"\']+)["\']'], p.text)
        if not base:
            continue
        base = absolute(p.url, base)
        if base:
            ch = item('xsport', name, base.rstrip('/') + '/' + cid + '/playlist.m3u8',
                      referer=home.url)
            if ch: result.append(ch)
    return result
