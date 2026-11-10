"""Site keşif katmanı. Doğrudan yayın/proxy sunmaz; sadece kaynak adayları üretir.

Tüm site istekleri sertifika doğrulayarak yapılır. HTTP başlıklarının web
sayfasını çekmek ve manifesti oynatmak için ayrı olduğuna dikkat edin.
"""
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import html
import ipaddress
import json
import logging
import re
from urllib.parse import urljoin, urlparse

import requests

from ..fetch import BROWSER_UA
from ..parse import Channel

log = logging.getLogger('site_providers')


@dataclass(frozen=True)
class Page:
    url: str
    text: str
    status: int = 200
    headers: dict = None


def safe_url(url):
    """Dışarıdan öğrenilen URL'lerde dahili ağ/kimlik bilgisi kullanımını engelle."""
    try:
        p = urlparse(url)
        if p.scheme not in ('https', 'http') or not p.hostname or p.username or p.password:
            return False
        host = p.hostname.lower().rstrip('.')
        if host == 'localhost' or host.endswith(('.localhost', '.local', '.internal')):
            return False
        try:
            addr = ipaddress.ip_address(host)
        except ValueError:
            return True
        return addr.is_global
    except (ValueError, TypeError):
        return False


def absolute(base, path):
    if not path or not isinstance(path, str):
        return None
    target = html.unescape(path).replace('\\/', '/').strip()
    target = urljoin(base, target)
    return target if safe_url(target) else None


def hls_url(value, base):
    url = absolute(base, value)
    if not url:
        return None
    # Başka uzantılı video/DRM bağlantılarını HLS gibi gösterme.
    if '.m3u8' not in urlparse(url).path.lower():
        return None
    return url


class Client:
    """En fazla 3 güvenli yönlendirme; 512 KB HTML, öngörülebilir timeout."""
    def __init__(self, timeout=8, session=None):
        self.timeout = min(max(float(timeout), 1.0), 20.0)
        self.session = session or requests.Session()
        self.session.headers.update({'User-Agent': BROWSER_UA,
                                     'Accept': 'text/html,application/json,*/*'})

    def get(self, url, headers=None):
        if not safe_url(url):
            raise ValueError('Geçersiz veya dahili ağ hedefi')
        for _ in range(4):
            try:
                with self.session.get(url, timeout=(self.timeout / 2, self.timeout),
                                      headers=headers, allow_redirects=False, stream=True) as res:
                    if res.status_code in (301, 302, 303, 307, 308):
                        nxt = absolute(url, res.headers.get('Location'))
                        if not nxt:
                            raise ValueError('Güvensiz yönlendirme')
                        url = nxt
                        continue
                    if res.status_code != 200:
                        return Page(url, '', res.status_code, dict(res.headers))
                    data = bytearray()
                    for part in res.iter_content(32768):
                        data.extend(part)
                        if len(data) > 512_000:
                            raise ValueError('Site cevabı aşırı büyük')
                    enc = res.encoding or 'utf-8'
                    return Page(url, data.decode(enc, errors='replace'), 200, dict(res.headers))
            except requests.RequestException as exc:
                raise ValueError(type(exc).__name__) from exc
        raise ValueError('Yönlendirme sınırı aşıldı')


def pick(patterns, text, flags=re.I | re.S):
    for pat in patterns:
        m = re.search(pat, text or '', flags)
        if m:
            return html.unescape(m.group(1).replace('\\/', '/'))
    return None


def extract_stream(payload, base):
    """JSON içindeki HLS alanlarını arar; değilse düz JS URL değerini okur."""
    def find(node, depth=0):
        if depth > 5:
            return None
        if isinstance(node, str):
            return hls_url(node, base)
        if isinstance(node, dict):
            for key in ('stream', 'url', 'source', 'deismackanal', 'file', 'hls', 'src'):
                if key in node:
                    got = find(node[key], depth + 1)
                    if got:
                        return got
            for val in node.values():
                got = find(val, depth + 1)
                if got:
                    return got
        elif isinstance(node, list):
            for val in node[:80]:
                got = find(val, depth + 1)
                if got:
                    return got
        return None
    try:
        result = find(json.loads(payload))
        if result:
            return result
    except (TypeError, ValueError):
        pass
    match = pick([r'["\'](?:stream|url|source|deismackanal|file|hls|src)["\']\s*:\s*["\']([^"\']+\.m3u8(?:\?[^"\']*)?)["\']',
                  r'\b(?:streamUrl|sourceUrl)\s*=\s*["\']([^"\']+\.m3u8(?:\?[^"\']*)?)["\']'], payload)
    return hls_url(match, base) if match else None


def item(provider, name, stream, referer='', origin='', ua=BROWSER_UA):
    url = hls_url(stream, stream) if stream else None
    if not url:
        return None
    headers = {'User-Agent': ua}
    if referer:
        headers['Referer'] = referer
    if origin:
        headers['Origin'] = origin
    ch = Channel(name=name, url=url, group='TR-SPOR', source=f'site:{provider}', headers=headers)
    ch.src_group = 'TR-SPOR'
    return ch


def origin_of(url):
    p = urlparse(url)
    return f'{p.scheme}://{p.netloc}'


def try_get(client, url, headers=None):
    if not url:
        return None
    try:
        p = client.get(url, headers=headers)
        return p if p.status == 200 else None
    except (ValueError, OSError) as e:
        log.debug('Site erişimi başarısız (%s)', type(e).__name__)
        return None


def candidates(conf):
    """Önce sabit adresler; isteğe bağlı desenle dönen alan adlarından sınırlı arama.

    Domain döndürme özelliği kapatılabilir. Varsayılan tarama aralığından en fazla
    50 aday seçilir, ağ trafiği sınırlı tutulur; tüm alan adları taranmaz.
    """
    values = [conf.get('base_url', '')] + conf.get('domain_candidates', [])
    pattern = conf.get('domain_pattern', '')
    if pattern and '{n}' in pattern and conf.get('auto_domain_scan', False):
        first = int(conf.get('index_start', 1))
        last = int(conf.get('index_end', first))
        limit = min(max(int(conf.get('scan_limit', 20)), 0), 50)
        if last >= first and limit:
            span = last - first + 1
            if limit >= span:
                indexes = range(last, first - 1, -1)
            else:
                # Bir uçtaki yeni sürümler kadar aralığa yayılmış adaylar da denenir.
                tail = max(1, limit // 2)
                indexes = list(range(last, max(first - 1, last - tail), -1))
                rest = limit - len(indexes)
                if rest:
                    indexes += [first + ((span - 1) * i) // max(rest - 1, 1)
                                for i in range(rest)]
            for n in indexes:
                values.append(pattern.format(n=n))
    return list(dict.fromkeys(u for u in values if u and safe_url(u)))


def active_home(client, conf, required=None):
    urls = candidates(conf)
    def lookup(url):
        p = try_get(client, url)
        return p if p and (not required or any(x in p.text for x in required)) else None
    # İlk açıkça verilen URL tercih edilir, çoklu döner domainler sınırlı eşzamanlı denenir.
    direct = len(([conf.get('base_url')] if conf.get('base_url') else []) +
                 (conf.get('domain_candidates') or []))
    for url in urls[:direct]:
        page = lookup(url)
        if page:
            return page
    todo = urls[direct:]
    if not todo:
        return None
    with ThreadPoolExecutor(max_workers=min(8, len(todo))) as pool:
        results = list(pool.map(lookup, todo))
    return next((r for r in results if r), None)
