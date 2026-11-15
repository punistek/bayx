#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Canlı maç listesi (maclar.json) — ana motordan BAĞIMSIZ, hafif ve hızlı (≈30 sn).
.github/workflows/spor.yml 2 saatte bir çalıştırır.

    python sports_update.py               # EPG_URLS (ortam değişkeni) ya da config'deki adresler
    python sports_update.py --dry-run     # dosya yazmadan dene, bulduklarını yazdır

Akış okunamazsa eski maclar.json'a DOKUNULMAZ (uygulama son iyi listeyle devam eder).
"""
import argparse
import logging
import sys
import time


def main():
    ap = argparse.ArgumentParser(description="Canlı maç listesi")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out", default="maclar.json")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                        datefmt="%H:%M:%S")
    from engine import config as C
    from engine.fetch import make_session
    from engine import sports_epg as S

    now = int(time.time())
    matches = S.build(C.EPG_URLS, make_session(retries=2), now=now)
    if matches is None:
        logging.error("Hiçbir yayın akışı okunamadı; maclar.json değiştirilmedi.")
        return 0
    canli = [m for m in matches if m["bas"] <= now < m["bit"]]
    logging.info("Bulunan maç: %d (şu an %d)", len(matches), len(canli))
    for m in matches[:40]:
        logging.info("  %s · %s · %s · %s", time.strftime("%d.%m %H:%M", time.localtime(m["bas"])),
                     m["kanal"], m["baslik"], m["lig"])
    if not a.dry_run:
        S.write(a.out, matches, now)
    return 0


if __name__ == "__main__":
    sys.exit(main())
