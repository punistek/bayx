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


SKIPPED = {"foreign": 0, "capped": 0}
_TR_FILE_HINTS = ("turk", "turkiye", "turkey", "tr", "tur", "trt", "kanal", "ulusal", "yerel",
                  "canli", "spor", "haber", "ulke")


def foreign_path(path):
    """Dosya yolu yabancı ülke/dil listesi mi? (ör. eng/business.m3u, us.m3u, countries/de.m3u)"""
    low = path.lower()
    parts = re.split(r"[/]", low)
    for seg in parts[:-1]:
        if seg in C.FOREIGN_PATH_CODES:
            return True
    stem = re.sub(r"\.m3u8?$", "", parts[-1])
    head = re.split(r"[_\-.]", stem)[0]
    return stem in C.FOREIGN_PATH_CODES or (head in C.FOREIGN_PATH_CODES and len(head) <= 3)


def tr_path_score(path):
    toks = set(re.split(r"[^a-z0-9]+", path.lower()))
    return sum(2 for h in _TR_FILE_HINTS if h in toks) + sum(1 for h in _TR_FILE_HINTS
                                                              if len(h) > 3 and h in path.lower())


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


def repo_m3u_urls(owner, repo, branch=None, subdir="", auto=False):
    """Bir depodaki tüm m3u/m3u8 dosyalarının raw adresleri.
    auto=True (aramadan gelen depo): yabancı ülke/dil dosyaları atlanır, TR'ye en yakın
    MAX_FILES_PER_REPO dosya alınır. Elle eklenen depolarda (sources.txt) hepsi alınır."""
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
        picked = [f for f in files
                  if f.lower().endswith(M3U_EXT) and (not sub or f.startswith(sub + "/") or f == sub)]
        if auto:
            n0 = len(picked)
            picked = [f for f in picked if not foreign_path(f)]
            SKIPPED["foreign"] += n0 - len(picked)
            picked.sort(key=tr_path_score, reverse=True)
            if len(picked) > C.MAX_FILES_PER_REPO:
                SKIPPED["capped"] += len(picked) - C.MAX_FILES_PER_REPO
                picked = picked[:C.MAX_FILES_PER_REPO]
        return [_raw(owner, repo, b, f) for f in picked]
    return []


def gist_m3u_urls(user, gid):
    j = get_json(f"https://api.github.com/gists/{gid}", headers=gh_headers())
    if not j:
        return [f"https://gist.githubusercontent.com/{user}/{gid}/raw"]
    return [f["raw_url"] for name, f in (j.get("files") or {}).items()
            if name.lower().endswith(M3U_EXT) or "mpegurl" in (f.get("type") or "")]


SLUG_RE = re.compile(r"^([\w.-]+)/([\w.-]+)$")


def expand(url):
    """Bir sources.txt satırını bir veya daha fazla doğrudan m3u adresine çevir."""
    url = url.strip()
    m = SLUG_RE.match(url)
    if m:                                   # "kullanici/depo" kısaltması
        return repo_m3u_urls(*m.groups())
    m = GH_RE.match(url)
    if m:
        o, r, mode, b, path = m.groups()
        path = (path or "").lstrip("/")
        if mode in ("blob", "raw") and path:
            return [_raw(o, r, b, path)]
        return repo_m3u_urls(o, r, b, path)   # elle eklenen: filtresiz
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
            repo = (it.get("repository") or {}).get("full_name")
            path = it.get("path", "")
            if not repo or not path or foreign_path(path):
                continue
            # Commit'e sabitlenmiş adres yerine HEAD: dosya güncellendikçe yeni hali gelir
            out.add(f"https://raw.githubusercontent.com/{repo}/HEAD/{_q(path)}")
    return list(out)


# ------------------------------------------------------------------ hepsi
def manual_lines():
    if not os.path.exists(C.SOURCES_FILE):
        return []
    out = []
    with open(C.SOURCES_FILE, encoding="utf-8") as f:
        for ln in f:
            ln = ln.split(" #", 1)[0].strip()
            if ln and not ln.startswith("#") and (ln.lower().startswith("http") or SLUG_RE.match(ln)):
                out.append(ln)
    return out


def collect_all(search=True, source_state=None):
    """Döndürür: [(m3u_url, tür)] — benzersiz."""
    SKIPPED.update(foreign=0, capped=0)
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
            for lst in ex.map(lambda t: repo_m3u_urls(*t, auto=True), repos):
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
    if SKIPPED["foreign"] or SKIPPED["capped"]:
        log.info("Yabancı ülke/dil dosyası atlandı: %d · depo başı sınır nedeniyle atlanan: %d",
                 SKIPPED["foreign"], SKIPPED["capped"])
    log.info("Toplam benzersiz m3u kaynağı: %d", len(out))
    return out
