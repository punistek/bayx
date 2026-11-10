# -*- coding: utf-8 -*-
"""
Aday m3u kaynaklarını toplar:

  sources.txt (elle)  — her satıra bir adres. Desteklenen biçimler:
      https://.../liste.m3u                       → doğrudan m3u
      https://github.com/kullanici/depo           → depodaki TÜM .m3u/.m3u8 dosyaları
      https://github.com/kullanici/depo/tree/dal/klasor   → o klasördeki dosyalar
      https://github.com/kullanici/depo/blob/dal/a.m3u    → raw adrese çevrilir
      https://gist.github.com/kullanici/abc123     → gist içindeki m3u dosyaları
  CURATED_SOURCES     — config.py'deki bilinen açık kaynaklar
  GitHub depo/konu araması — son X günde güncellenen TR iptv depoları
  GitHub kod araması (token gerekir) — taze .m3u dosyaları

Çıktı: [(url, tür)]  tür: manual | curated | auto
"""
import logging
import os
import re
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from . import config as C
from .fetch import get_json, gh_headers

log = logging.getLogger("sources")

GH_RE = re.compile(r"^https?://(?:www\.)?github\.com/([^/\s]+)/([^/\s#?]+)(?:/(tree|blob|raw)/([^/\s]+)(/[^\s#?]*)?)?/?$", re.I)
GIST_RE = re.compile(r"^https?://gist\.github(?:usercontent)?\.com/([^/\s]+)/([0-9a-f]{8,})", re.I)
M3U_EXT = (".m3u", ".m3u8")


def _q(path):
    return urllib.parse.quote(path.lstrip("/"), safe="/")


def _raw(o, r, b, path):
    return f"https://raw.githubusercontent.com/{o}/{r}/{_q(b)}/{_q(path)}"


# ------------------------------------------------------------------ depo dosyaları
def _default_branch(o, r):
    j = get_json(f"https://api.github.com/repos/{o}/{r}", headers=gh_headers())
    return (j or {}).get("default_branch")


def _list_jsdelivr(o, r, b):
    j = get_json(f"https://data.jsdelivr.com/v1/packages/gh/{o}/{r}@{_q(b)}?structure=flat")
    if not j:
        return None
    return [f["name"].lstrip("/") for f in j.get("files", [])]


def _list_gh_tree(o, r, b):
    j = get_json(f"https://api.github.com/repos/{o}/{r}/git/trees/{_q(b)}?recursive=1",
                 headers=gh_headers())
    if not j:
        return None
    return [t["path"] for t in j.get("tree", []) if t.get("type") == "blob"]


def repo_m3u_urls(owner, repo, branch=None, subdir=""):
    """Bir depodaki tüm m3u/m3u8 dosyalarının raw adresleri."""
    repo = repo.removesuffix(".git")
    branches = [branch] if branch else [b for b in (_default_branch(owner, repo), "main", "master") if b]
    seen = set()
    for b in branches:
        if b in seen:
            continue
        seen.add(b)
        files = _list_jsdelivr(owner, repo, b)
        if files is None:
            files = _list_gh_tree(owner, repo, b)
        if not files:
            continue
        sub = subdir.strip("/")
        out = [_raw(owner, repo, b, f) for f in files
               if f.lower().endswith(M3U_EXT) and (not sub or f.startswith(sub + "/") or f == sub)]
        return out
    return []


def gist_m3u_urls(user, gid):
    j = get_json(f"https://api.github.com/gists/{gid}", headers=gh_headers())
    if not j:
        return [f"https://gist.githubusercontent.com/{user}/{gid}/raw"]
    return [f["raw_url"] for name, f in (j.get("files") or {}).items()
            if name.lower().endswith(M3U_EXT) or "mpegurl" in (f.get("type") or "")]


def expand(url):
    """Bir sources.txt satırını bir veya daha fazla doğrudan m3u adresine çevir."""
    url = url.strip()
    m = GH_RE.match(url)
    if m:
        o, r, mode, b, path = m.groups()
        path = (path or "").lstrip("/")
        if mode in ("blob", "raw") and path:
            return [_raw(o, r, b, path)]
        return repo_m3u_urls(o, r, b, path)
    g = GIST_RE.match(url)
    if g and "/raw" not in url:
        return gist_m3u_urls(*g.groups())
    return [url]


# ------------------------------------------------------------------ GitHub araması
def _since():
    return (datetime.now(timezone.utc) - timedelta(days=C.RECENT_DAYS)).strftime("%Y-%m-%d")


def gh_search_repos():
    repos = {}
    queries = [f"{t} pushed:>={_since()}" for t in C.SEARCH_TERMS] + \
              [f"{t} pushed:>={_since()}" for t in C.TOPIC_SEARCH]
    for q in queries:
        url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode(
            {"q": q, "sort": "updated", "order": "desc", "per_page": 40})
        j = get_json(url, headers=gh_headers())
        if not j:
            continue
        for it in j.get("items", []):
            if it.get("archived") or it.get("fork") and not it.get("stargazers_count"):
                continue
            repos.setdefault(it["full_name"], (it["owner"]["login"], it["name"],
                                               it.get("default_branch") or "main"))
    return list(repos.values())[:C.MAX_REPOS]


def gh_search_code():
    if not C.GITHUB_TOKEN:
        log.info("GITHUB_TOKEN yok → kod araması atlandı")
        return []
    out = set()
    for term in C.CODE_SEARCH_TERMS:
        url = "https://api.github.com/search/code?" + urllib.parse.urlencode({"q": term, "per_page": 30})
        j = get_json(url, headers=gh_headers())
        for it in (j or {}).get("items", []):
            html = it.get("html_url", "")
            if "/blob/" in html:
                out.add(html.replace("https://github.com/", "https://raw.githubusercontent.com/", 1)
                        .replace("/blob/", "/", 1))
    return list(out)


# ------------------------------------------------------------------ hepsi
def manual_lines():
    if not os.path.exists(C.SOURCES_FILE):
        return []
    out = []
    with open(C.SOURCES_FILE, encoding="utf-8") as f:
        for ln in f:
            ln = ln.split(" #", 1)[0].strip()
            if ln and not ln.startswith("#") and ln.lower().startswith("http"):
                out.append(ln)
    return out


def collect_all(search=True, source_state=None):
    """Döndürür: [(m3u_url, tür)] — benzersiz."""
    found = {}

    def add(urls, kind):
        for u in urls:
            if u and u not in found:
                found[u] = kind

    manual = manual_lines()
    with ThreadPoolExecutor(max_workers=C.THREADS_FETCH) as ex:
        for lst in ex.map(expand, manual):
            add(lst, "manual")
    log.info("sources.txt: %d satır → %d m3u dosyası", len(manual), len(found))
    add(C.CURATED_SOURCES, "curated")

    if search and C.SEARCH_ENABLED:
        repos = gh_search_repos()
        log.info("GitHub aramasında %d depo bulundu, dosyalar listeleniyor...", len(repos))
        with ThreadPoolExecutor(max_workers=C.THREADS_FETCH) as ex:
            for lst in ex.map(lambda t: repo_m3u_urls(*t), repos):
                add(lst, "auto")
        code = gh_search_code()
        if code:
            log.info("Kod aramasından %d dosya", len(code))
        add(code, "auto")

    out = []
    skipped = 0
    for u, kind in found.items():
        if kind == "auto" and source_state and source_state.quarantined(u):
            skipped += 1
            continue
        out.append((u, kind))
    if skipped:
        log.info("Karantinadaki (verimsiz) %d kaynak bu tur atlandı", skipped)
    log.info("Toplam benzersiz m3u kaynağı: %d", len(out))
    return out
