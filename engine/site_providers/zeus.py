"""Zeus / Bonus TV: ch.html?id= -> streamUrl tabanı -> /id/index.m3u8."""
from .common import absolute, active_home, item, pick, try_get

CHANNELS = {
    'b1':'beIN Sports 1', 'b2':'beIN Sports 2', 'b3':'beIN Sports 3',
    'b4':'beIN Sports 4', 'bein5':'beIN Sports 5',
    's1':'S Sport 1', 's2':'S Sport 2',
    'smart1':'Smart Spor 1', 'smart2':'Smart Spor 2',
    'tivibu1':'Tivibu Spor 1', 'tivibu2':'Tivibu Spor 2',
    'tivibu3':'Tivibu Spor 3', 'euro1':'Eurosport 1',
    'euro2':'Eurosport 2', 'tabii1':'Tabii Spor 1',
    'tabii2':'Tabii Spor 2', 'tabii3':'Tabii Spor 3',
    'tabii4':'Tabii Spor 4', 'tabii5':'Tabii Spor 5',
}


def discover(client, conf):
    home = active_home(client, conf)
    if not home:
        return []
    page = try_get(client, absolute(home.url, '/ch.html?id=b1'), {'Referer': home.url})
    if not page:
        return []
    base = pick([r'\b(?:var\s+)?streamUrl\s*=\s*["\']([^"\']+)["\']'], page.text)
    base = absolute(page.url, base) if base else None
    if not base:
        return []
    result = []
    for cid, name in (conf.get('channels') or CHANNELS).items():
        ch = item('zeus', name, base.rstrip('/') + '/' + cid + '/index.m3u8', referer=home.url)
        if ch: result.append(ch)
    return result
