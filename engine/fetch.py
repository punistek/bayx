# -*- coding: utf-8 -*-
"""HTTP oturumu ve ortak indirme yardımcıları."""
import socket
import requests
from requests.adapters import HTTPAdapter
import urllib3

from . import config as C

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
socket.setdefaulttimeout(C.HTTP_TIMEOUT + 3)

# Tarayıcı gibi görün (bazı CDN'ler ham istekleri reddeder).
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) "
              "Gecko/20100101 Firefox/115.0")
# Oynatıcı gibi görün (yayın testinde daha gerçekçi).
PLAYER_UA = "VLC/3.0.20 LibVLC/3.0.20"


def make_session(ua=BROWSER_UA):
    s = requests.Session()
    ad = HTTPAdapter(pool_connections=100, pool_maxsize=100, max_retries=0)
    s.mount("http://", ad)
    s.mount("https://", ad)
    s.headers.update({"User-Agent": ua})
    s.verify = False
    return s


# Paylaşımlı oturumlar (thread-safe: requests.Session thread'ler arası okuma için güvenli).
SESSION = make_session(BROWSER_UA)
PLAYER = make_session(PLAYER_UA)


def get_text(url, timeout=None, session=None):
    """Bir URL'yi metin olarak indir; başarısızsa None."""
    s = session or SESSION
    try:
        r = s.get(url, timeout=timeout or C.HTTP_TIMEOUT, allow_redirects=True)
        if r.status_code in (200, 301, 302):
            return r.text
    except requests.RequestException:
        return None
    return None


def gh_headers():
    h = {"Accept": "application/vnd.github+json", "User-Agent": BROWSER_UA}
    if C.GITHUB_TOKEN:
        h["Authorization"] = "Bearer " + C.GITHUB_TOKEN
    return h
