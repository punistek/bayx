# -*- coding: utf-8 -*-
"""Akışı yönetir: topla → ayrıştır → temizle → tekille → canlılık testi → yaz → raporla."""
import logging
import os
import shutil
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from . import config as C
from . import clean, parse, sources
from .fetch import get_text
from .liveness import is_alive

log = logging.getLogger("build")


def load_armor():
    """zirhli.m3u — elle bakımlı kanallar. BİREBİR korunur (logo/grup/sıra bozulmaz),
    test edilmez, aynen en üste eklenir. Döndürür: (ham_metin_bloğu, url_kümesi)."""
    if not os.path.exists(C.ARMOR_FILE):
        return "", set()
    raw = open(C.ARMOR_FILE, encoding="utf-8").read()
    # baştaki #EXTM3U satırını çıkar, gerisini aynen tut
    lines = [ln for ln in raw.splitlines()]
    if lines and lines[0].strip().upper().startswith("#EXTM3U"):
        lines = lines[1:]
    block = "\n".join(lines).strip("\n")
    chans = parse.parse(raw)           # sadece URL'leri çıkarmak için
    urls = {c.url.strip() for c in chans}
    log.info("Zırhlı liste: %d kanal (birebir korunuyor, test edilmez)", len(chans))
    return block, urls


def fetch_source(url):
    txt = get_text(url, timeout=C.HTTP_TIMEOUT)
    if not txt or "#EXTINF" not in txt:
        return []
    return parse.parse(txt, source=url)


def gather_candidates(armor_urls):
    """Tüm kaynakları indir, ayrıştır, temizle, tekille. Zırhlıda olan URL'leri atla."""
    src_urls = sources.collect_all()
    all_chans = []
    with ThreadPoolExecutor(max_workers=C.THREADS_FETCH) as ex:
        for chans in ex.map(fetch_source, src_urls):
            all_chans.extend(chans)
    log.info("Ham kanal (tüm kaynaklar): %d", len(all_chans))

    refined = clean.refine(all_chans)
    log.info("Kalite kapısından geçen: %d", len(refined))

    refined = [c for c in refined if c.url.strip() not in armor_urls]
    unique = clean.dedupe(refined)
    log.info("Tekilleştirme sonrası aday: %d", len(unique))

    if len(unique) > C.MAX_TEST:
        unique.sort(key=clean.tr_score, reverse=True)
        unique = unique[:C.MAX_TEST]
        log.info("En iyi %d aday test edilecek", C.MAX_TEST)
    return unique


def test_liveness(cands):
    """Adayları eş zamanlı test et, canlı olanları döndür."""
    log.info("Canlılık testi başlıyor (%d aday, %d eş zaman)...", len(cands), C.THREADS_TEST)
    alive = []
    done = 0
    with ThreadPoolExecutor(max_workers=C.THREADS_TEST) as ex:
        futs = {ex.submit(is_alive, c.url): c for c in cands}
        for fut in futs:
            pass
        from concurrent.futures import as_completed
        for fut in as_completed(futs):
            c = futs[fut]
            done += 1
            try:
                c.alive = fut.result()
            except Exception:
                c.alive = False
            if c.alive:
                alive.append(c)
            if done % 200 == 0:
                log.info("  test: %d/%d  (canlı: %d)", done, len(cands), len(alive))
    log.info("Test bitti. Canlı: %d / %d", len(alive), len(cands))
    return alive


def order(channels):
    """Gruba ve TR puanına göre düzenli sırala."""
    group_order = [g for g, _ in C.GROUP_RULES] + [C.DEFAULT_GROUP]
    idx = {g: i for i, g in enumerate(group_order)}
    return sorted(channels, key=lambda c: (idx.get(c.group, 99), -clean.tr_score(c), c.name))


def _count_extinf(block):
    return sum(1 for ln in block.splitlines() if ln.startswith("#EXTINF"))


def write_outputs(armor_block, fresh):
    # tr.m3u
    if os.path.exists(C.TR_FILE):
        shutil.copyfile(C.TR_FILE, C.TR_FILE + ".bak")
    armor_n = _count_extinf(armor_block)
    stamp = datetime.now().strftime("%d-%m-%Y %H:%M")
    parts = ["#EXTM3U"]
    if armor_block:
        parts.append(armor_block)
    parts.append(f"# --- GÜNCEL CANLI LİSTE ({stamp}) · {len(fresh)} kanal --- #")
    for c in fresh:
        parts.append(c.to_m3u())
    open(C.TR_FILE, "w", encoding="utf-8").write("\n".join(parts) + "\n")

    # rapor
    groups = Counter(c.group for c in fresh)
    rep = ["# AkcagozTV Canlı — Güncelleme Raporu",
           f"\n**Tarih:** {stamp}",
           f"\n**Zırhlı (korunan):** {armor_n} kanal",
           f"**Yeni bulunan canlı:** {len(fresh)} kanal",
           f"**Toplam:** {armor_n + len(fresh)} kanal\n",
           "## Gruplara göre yeni canlı kanallar\n"]
    for g, n in sorted(groups.items(), key=lambda x: -x[1]):
        rep.append(f"- **{g}:** {n}")
    open(C.REPORT_FILE, "w", encoding="utf-8").write("\n".join(rep) + "\n")
    log.info("Yazıldı → %s (%d kanal) ve %s", C.TR_FILE, armor_n + len(fresh), C.REPORT_FILE)


def run():
    t0 = datetime.now()
    armor, armor_urls = load_armor()
    cands = gather_candidates(armor_urls)
    if not cands:
        log.warning("Aday kanal bulunamadı. Zırhlı liste korunuyor.")
    alive = test_liveness(cands) if cands else []
    before = len(alive)
    alive = clean.cap_by_name(alive)          # aynı kanalın fazla kopyasını kırp
    if before != len(alive):
        log.info("İsim tekilleştirme: %d → %d (fazla kopyalar atıldı)", before, len(alive))
    alive = order(alive)
    write_outputs(armor, alive)
    log.info("BİTTİ · süre: %s", str(datetime.now() - t0).split(".")[0])
    return len(armor), len(alive)
