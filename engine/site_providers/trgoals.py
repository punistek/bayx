"""TRGoals: sayfa scraper değil; kullanıcı tarafından girilmiş Worker HLS bağlantı listesi."""
from .common import item


def discover(client, conf):
    result = []
    for ch in conf.get('streams', []):
        if not isinstance(ch, dict):
            continue
        out = item('trgoals', ch.get('name', 'TRGoals'), ch.get('url'),
                   referer=ch.get('referer', ''), origin=ch.get('origin', ''))
        if out: result.append(out)
    return result
