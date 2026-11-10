"""Atom: /matches?id= -> JS fetch() -> JSON HLS URL."""
from .common import absolute, candidates, extract_stream, item, origin_of, pick, try_get

CHANNELS = {
    'bein-sports-1':'beIN Sports 1', 'bein-sports-2':'beIN Sports 2',
    'bein-sports-3':'beIN Sports 3', 'bein-sports-4':'beIN Sports 4',
    's-sport':'S Sport 1', 's-sport-2':'S Sport 2',
    'tivibu-spor-1':'Tivibu Spor 1', 'tivibu-spor-2':'Tivibu Spor 2',
    'tivibu-spor-3':'Tivibu Spor 3', 'trt-spor':'TRT Spor',
    'trt-yildiz':'TRT Spor Yıldız', 'trt1':'TRT 1', 'aspor':'A Spor'
}


def discover(client, conf):
    # Yönlendirme bir reklam/ara sayfada bitebilir; diğer bilinen domainleri de dene.
    result = []
    seen_domains = set()
    for homepage in candidates(conf):
        home = try_get(client, homepage)
        if not home:
            continue
        domain = origin_of(home.url)
        if domain in seen_domains:
            continue
        seen_domains.add(domain)
        for cid, name in (conf.get('channels') or CHANNELS).items():
            p = try_get(client, f'{domain}/matches?id={cid}', {'Referer': home.url})
            if not p:
                continue
            call = pick([r'fetch\(\s*["\']([^"\']+)["\']'], p.text)
            if not call:
                continue
            # Bazı sayfalar /api/stream?id= gibi tamamlanmamış parametre veriyor.
            if conf.get('append_id', True) and call.endswith(('=', '/', '?')):
                call += cid
            api = absolute(p.url, call)
            obj = try_get(client, api, {'Referer': domain + '/', 'Origin': domain})
            if not obj:
                continue
            stream = extract_stream(obj.text, obj.url)
            ch = item('atom', name, stream, referer=domain + '/', origin=domain)
            if ch: result.append(ch)
        if result:
            break
    return result
