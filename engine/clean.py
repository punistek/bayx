# -*- coding: utf-8 -*-
"""Kalite kapısı: saçma/yabancı/VOD kanalları eler, isimleri temizler, gruplar, sıralar.
Ayrıca kullanıcı adı/şifre taşıyan adresleri (Xtream panelleri vb.) tespit eder."""
import re
import unicodedata
from urllib.parse import parse_qs, urlsplit

from . import config as C

# Yasaklı kelimeleri tek hızlı regex'te topla.
_BANNED_RE = re.compile(
    "(" + "|".join(re.escape(w) for w in sorted(C.YASAKLI_SET, key=len, reverse=True)) + ")",
    re.IGNORECASE)


def fold(s):
    """Türkçe karakterleri sadeleştir, küçük harfe indir (karşılaştırma için)."""
    s = (s or "").replace("ı", "i").replace("İ", "i")
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def is_banned(ch):
    """Yetişkin / yabancı / VOD / radyo ise True döner (listeye alınmaz)."""
    blob = f"{ch.name} {ch.group}"
    if _BANNED_RE.search(blob):
        return True
    low = ch.url.lower()
    if any(h in low for h in C.VOD_URL_HINTS):
        return True
    if C.VOD_NAME_RE.search(ch.name):
        return True
    return False


_DIGITS_RE = re.compile(r"^\d+(\.(ts|m3u8|mp4|mkv))?$", re.I)


def has_credentials(url):
    """Adres bir hesaba ait kullanıcı adı/şifre taşıyor mu?
    - http://user:pass@host/...
    - ...?username=..&password=..   (get.php, player_api.php)
    - Xtream: /live/USER/PASS/123.ts  ya da  /USER/PASS/123
    """
    try:
        p = urlsplit(url.strip())
    except ValueError:
        return False
    if p.username or p.password:
        return True
    if p.query:
        keys = {k.lower() for k in parse_qs(p.query, keep_blank_values=True)}
        if keys & C.CRED_QUERY_KEYS:
            return True
    path = p.path.lower()
    if path.endswith(("/get.php", "/player_api.php", "/xmltv.php", "/panel_api.php")):
        return True
    segs = [s for s in p.path.split("/") if s]
    if len(segs) == 4 and segs[0].lower() == "live" and _DIGITS_RE.match(segs[3]):
        return True
    if (len(segs) == 3 and _DIGITS_RE.match(segs[2])
            and segs[0].lower() not in C.CRED_PATH_SKIP
            and segs[1].lower() not in C.CRED_PATH_SKIP
            and not _DIGITS_RE.match(segs[0])):
        return True
    return False


def is_junk_name(name):
    """SVG logo kodu / data URI / URL gibi kanal adı olmayan çöpü yakala."""
    if not name:
        return True
    if C.JUNK_NAME_RE.search(name):
        return True
    letters = sum(c.isalpha() for c in name)
    if len(name) >= 8 and letters / max(1, len(name)) < C.MIN_LETTER_RATIO:
        return True
    return False


_URL_SKIP = {"index", "playlist", "live", "stream", "streams", "hls", "chunklist",
             "master", "tracks", "manifest", "mono", "video", "out", "ts", "m3u8",
             "m3u", "play", "channel", "ch", "tv", "get", "api", "cdn", "edge"}


def name_from_url(url):
    """Yayın adresinden okunabilir bir kanal adı türet (isim çöpse yedek plan)."""
    try:
        from urllib.parse import urlparse
        p = urlparse(url)
        parts = [seg for seg in p.path.split("/") if seg]
        for seg in reversed(parts):
            base = re.sub(r"\.(m3u8?|ts|mp4|php)$", "", seg, flags=re.I)
            base = re.sub(r"[_\-+.]", " ", base)
            base = re.sub(r"\b\d{2,}\b", " ", base)          # uzun sayıları at
            words = [w for w in base.split() if w and fold(w) not in _URL_SKIP]
            cand = " ".join(words).strip()
            if len(re.sub(r"[^a-zçğıöşü]", "", cand, flags=re.I)) >= 3:
                return cand.upper()[:C.MAX_NAME_LEN]
        host = (p.hostname or "").split(".")
        host = [h for h in host if h not in ("www", "com", "net", "tv", "org", "live")]
        if host:
            return host[0].upper()[:C.MAX_NAME_LEN]
    except Exception:
        pass
    return ""


def recover_name(ch):
    """İsim çöpse: önce tvg-id, sonra adresten türet. Bulamazsan '' döner."""
    if ch.tvg_id and not is_junk_name(ch.tvg_id):
        c = clean_name(ch.tvg_id)
        if c and len(c) >= 2 and not is_junk_name(c):
            return c[:C.MAX_NAME_LEN]
    return name_from_url(ch.url)


def clean_name(name):
    """Addan kalite/site/emoji takılarını söküp düzgün biçime getir."""
    original = name
    # korunacak isimleri geçici işaretle
    placeholders = {}
    for i, keep in enumerate(C.KEEP_WHOLE):
        rx = re.compile(re.escape(keep), re.IGNORECASE)
        if rx.search(name):
            tag = f"__KEEP{i}__"
            name = rx.sub(tag, name)
            placeholders[tag] = keep.upper()

    name = C.PREFIX_RE.sub("", name)
    name = C.BRACKETS_RE.sub(" ", name)
    name = C.YEDEK_GLUED_RE.sub(" ", name.strip())
    name = C.SITE_RE.sub(" ", name)
    name = C.STRIP_TAGS_RE.sub(" ", name)
    name = C.SYMBOL_RE.sub(" ", name)
    name = C.MULTISPACE_RE.sub(" ", name).strip()

    for tag, val in placeholders.items():
        name = name.replace(tag, val)

    name = C.MULTISPACE_RE.sub(" ", name).strip().upper()
    return name or original.strip().upper()


def assign_group(ch):
    blob = fold(f"{ch.name} {ch.group}")
    for gname, keys in C.GROUP_RULES:
        if any(fold(k) in blob for k in keys):
            return gname
    return C.DEFAULT_GROUP


def tr_score(ch):
    blob = fold(f"{ch.name} {ch.group} {ch.source}")
    toks = set(re.split(r"[^a-z0-9]+", blob))
    score = 0
    for h in C.TR_HINTS:
        hf = fold(h)
        if hf in toks:
            score += 2
        elif len(hf) > 2 and hf in blob:
            score += 1
    return score


def norm_name_key(name):
    """İki kanal 'aynı' mı? Kalite takısı sökülmüş sade ada bakarız."""
    k = fold(clean_name(name))
    k = re.sub(r"[^a-z0-9]+", "", k)
    return k


def refine(channels, stats=None):
    """Yasaklıları ele, isimleri temizle, grupla. (Henüz tekilleştirme/test yok.)"""
    out = []
    stats = stats if stats is not None else {}
    for ch in channels:
        if not ch.url or not ch.url.lower().startswith(("http://", "https://")):
            continue
        if has_credentials(ch.url):
            stats["credential"] = stats.get("credential", 0) + 1
            continue
        if is_banned(ch):
            stats["banned"] = stats.get("banned", 0) + 1
            continue
        # İsim çöpse (SVG/data/URL) kanalı ATMA — çalışıyor olabilir, adını kurtar.
        if is_junk_name(ch.name):
            ch.name = recover_name(ch)
        else:
            ch.name = clean_name(ch.name)
        # Hâlâ kullanılabilir bir isim yoksa ancak o zaman at.
        if (not ch.name or len(ch.name) < 2 or len(ch.name) > C.MAX_NAME_LEN
                or is_junk_name(ch.name)):
            continue
        ch.group = assign_group(ch)
        out.append(ch)
    return out


def dedupe(channels):
    """Aynı URL'yi ve aynı kanalın tekrarını tekille. Önce URL, sonra isim bazlı."""
    seen_url, by_url = set(), []
    for ch in channels:
        u = ch.url.strip()
        if u in seen_url:
            continue
        seen_url.add(u)
        by_url.append(ch)
    return by_url
