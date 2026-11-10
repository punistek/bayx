# -*- coding: utf-8 -*-
"""HTTP oturumları ve ortak indirme yardımcıları.

Güvenlik: sertifika doğrulaması varsayılan olarak AÇIK. Kaynak listeleri (GitHub vb.)
her zaman doğrulanarak indirilir. Yayın testinde sertifikası bozuk sunucular ayrıca
'güvensiz' oturumla denenir ve puan cezası alır (uygulama bu yayını açamayabilir).
"""
import logging
import time

import requests
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from . import config as C

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
log = logging.getLogger("fetch")

BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
# Uygulamanın oynatıcısına benzer (Media3/ExoPlayer).
PLAYER_UA = "ExoPlayerLib/2.19.1 (Linux; Android 13) PuuStream"


def make_session(ua=BROWSER_UA, verify=True, retries=0):
    s = requests.Session()
    retry = Retry(total=retries, backoff_factor=0.6, status_forcelist=(429, 502, 503, 504),
                  allowed_methods=("GET", "HEAD")) if retries else 0
    ad = HTTPAdapter(pool_connections=64, pool_maxsize=128, max_retries=retry)
    s.mount("http://", ad)
    s.mount("https://", ad)
    s.headers.update({"User-Agent": ua, "Accept": "*/*"})
    s.verify = verify
    return s


SESSION = make_session(BROWSER_UA, verify=True, retries=2)        # kaynak indirme
PLAYER = make_session(PLAYER_UA, verify=True)                      # yayın testi
PLAYER_INSECURE = make_session(PLAYER_UA, verify=False)            # yalnızca TLS teşhisi


def get_text(url, timeout=None, session=None, max_bytes=None, headers=None):
    """URL'yi metin olarak indir; başarısızsa None. Boyut sınırı uygular."""
    s = session or SESSION
    max_bytes = max_bytes or C.MAX_SOURCE_BYTES
    try:
        with s.get(url, timeout=timeout or C.HTTP_TIMEOUT, allow_redirects=True,
                   stream=True, headers=headers) as r:
            if r.status_code != 200:
                return None
            buf = bytearray()
            for chunk in r.iter_content(65536):
                buf.extend(chunk)
                if len(buf) > max_bytes:
                    log.warning("Çok büyük, atlandı: %s", url)
                    return None
            enc = r.encoding or "utf-8"
            try:
                return buf.decode(enc, "replace")
            except LookupError:
                return buf.decode("utf-8", "replace")
    except requests.RequestException:
        return None


def get_json(url, timeout=None, headers=None):
    try:
        r = SESSION.get(url, timeout=timeout or C.HTTP_TIMEOUT, headers=headers)
        if r.status_code == 200:
            return r.json()
        if r.status_code in (403, 429) and "api.github.com" in url:
            reset = r.headers.get("X-RateLimit-Reset")
            log.warning("GitHub API limiti (%s). Sıfırlanma: %s", r.status_code,
                        time.strftime("%H:%M", time.localtime(int(reset))) if reset else "?")
    except (requests.RequestException, ValueError):
        pass
    return None


def gh_headers():
    h = {"Accept": "application/vnd.github+json", "User-Agent": BROWSER_UA,
         "X-GitHub-Api-Version": "2022-11-28"}
    if C.GITHUB_TOKEN:
        h["Authorization"] = "Bearer " + C.GITHUB_TOKEN
    return h
