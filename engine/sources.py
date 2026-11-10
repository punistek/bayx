# -*- coding: utf-8 -*-
"""
Aday m3u kaynaklarını toplar:
  - GitHub depo araması (son X günde güncellenmiş TR iptv depoları)
  - Depo içindeki m3u dosyalarını jsDelivr CDN ile listeler (API limitine takılmaz)
  - GitHub kod araması (token varsa taze .m3u dosyaları)
  - sources.txt + CURATED_SOURCES (elle eklenen bilinen kaynaklar)
Çıktı: benzersiz raw m3u URL listesi.
"""
import json
import logging
import os
import urllib.parse
from datetime import datetime, timedelta, timezone

from . import config as C
from .fetch import SESSION, gh_headers, get_text

log = logging.getLogger("sources")


def _q(path):
    return urllib.parse.quote(path.lstrip("/"), safe="/")


def gh_search_repos():
    """TR odaklı, yakın zamanda güncellenmiş m3u depolarını bul."""
    since = (datetime.now(timezone.utc) - timedelta(days=C.RECENT_DAYS)).strftime("%Y-%m-%d")
    repos = {}
    for term in C.SEARCH_TERMS:
        qstr = f"{term} pushed:>={since}"
        url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode(
            {"q": qstr, "sort": "updated", "order": "desc", "per_page": 40})
        try:
            r = SESSION.get(url, headers=gh_headers(), timeout=C.HTTP_TIMEOUT)
            if r.status_code != 200:
                log.warning("Depo araması %s: %s", r.status_code, term)
                continue
            for it in r.json().get("items", []):
                fn = it["full_name"]
                repos.setdefault(fn, dict(owner=it["owner"]["login"], repo=it["name"],
                                          branch=it.get("default_branch") or "main"))
        except Exception as e:
            log.warning("Depo araması hata: %s", e)
    return list(repos.values())[:C.MAX_REPOS]


def repo_m3u_urls(rep):
    """Bir deponun içindeki tüm m3u/m3u8 dosyalarını jsDelivr ile listele → raw URL'ler."""
    o, r, b = rep["owner"], rep["repo"], rep["branch"]
    api = f"https://data.jsdelivr.com/v1/packages/gh/{o}/{r}@{_q(b)}?structure=flat"
    txt = get_text(api, timeout=C.HTTP_TIMEOUT)
    urls = []
    if txt:
        try:
            for f in json.loads(txt).get("files", []):
                name = f["name"].lstrip("/")
                if name.lower().endswith((".m3u", ".m3u8")):
                    urls.append(f"https://raw.githubusercontent.com/{o}/{r}/{_q(b)}/{_q(name)}")
        except Exception:
            pass
    return urls


def gh_search_code():
    """Token varsa: taze .m3u dosyalarını kod aramasıyla bul."""
    if not C.GITHUB_TOKEN:
        return []
    out = []
    for term in C.CODE_SEARCH_TERMS:
        url = "https://api.github.com/search/code?" + urllib.parse.urlencode(
            {"q": f"{term} extension:m3u", "per_page": 20})
        try:
            r = SESSION.get(url, headers=gh_headers(), timeout=C.HTTP_TIMEOUT)
            if r.status_code != 200:
                continue
            for it in r.json().get("items", []):
                raw = it["html_url"].replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                out.append(raw)
        except Exception:
            continue
    return out


def file_sources():
    """sources.txt + CURATED_SOURCES."""
    urls = list(C.CURATED_SOURCES)
    if os.path.exists(C.SOURCES_FILE):
        with open(C.SOURCES_FILE, encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if ln and not ln.startswith("#") and ln.lower().startswith("http"):
                    urls.append(ln)
    return urls


def collect_all():
    """Tüm kaynaklardan benzersiz m3u URL listesi üret."""
    urls = set(file_sources())
    log.info("Sabit kaynak: %d", len(urls))

    repos = gh_search_repos()
    log.info("GitHub'da %d depo bulundu, m3u dosyaları listeleniyor...", len(repos))
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=C.THREADS_FETCH) as ex:
        for lst in ex.map(repo_m3u_urls, repos):
            urls.update(lst)

    code = gh_search_code()
    if code:
        log.info("Kod aramasından %d taze dosya", len(code))
        urls.update(code)

    log.info("Toplam benzersiz m3u kaynağı: %d", len(urls))
    return list(urls)
