# -*- coding: utf-8 -*-
"""Kalite kapısı: saçma/yabancı/VOD kanalları eler, isimleri temizler, gruplar, sıralar."""
import re
import unicodedata

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

    name = C.BRACKETS_RE.sub(" ", name)
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


def refine(channels):
    """Yasaklıları ele, isimleri temizle, grupla. (Henüz tekilleştirme/test yok.)"""
    out = []
    for ch in channels:
        if not ch.url or not ch.url.lower().startswith(("http://", "https://")):
            continue
        if is_banned(ch):
            continue
        ch.name = clean_name(ch.name)
        if not ch.name or len(ch.name) < 2:
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
