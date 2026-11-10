#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
puutv Canlı — otomatik canlı TV listesi güncelleyici.

Ne yapar:
  1. GitHub'da güncel Türkçe m3u depolarını arar (+ sources.txt kaynakları).
  2. Binlerce kanalı toplar, yasaklı/yabancı/VOD olanları eler, isimleri temizler.
  3. Her yayını GERÇEKTEN test eder; sadece canlı olanları tutar.
  4. zirhli.m3u'daki elle seçilmiş kanalları en üste koyar (asla test edilmez/silinmez).
  5. tr.m3u + RAPOR.md üretir.

Çalıştırma:
    python update_list.py              # tam otomasyon
    python update_list.py --test-only  # sadece mevcut tr.m3u'yu canlılık testinden geçir
    GITHUB_TOKEN=... python update_list.py   # arama limiti 5 kat artar (önerilir)
"""
import argparse
import logging
import sys


def setup_log():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S")


def main():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    setup_log()
    ap = argparse.ArgumentParser(description="puutv canlı TV listesi güncelleyici")
    ap.add_argument("--test-only", action="store_true",
                    help="Arama yapma; sadece mevcut tr.m3u'daki kanalları canlılık testinden geçir")
    args = ap.parse_args()

    from engine import build, parse, clean, config as C
    from engine.build import test_liveness, order, write_outputs, load_armor
    import os

    if args.test_only:
        logging.info("Sadece-test modu: mevcut %s süzülüyor", C.TR_FILE)
        armor, armor_urls = load_armor()
        chans = parse.parse(open(C.TR_FILE, encoding="utf-8").read()) if os.path.exists(C.TR_FILE) else []
        chans = [c for c in clean.refine(chans) if c.url.strip() not in armor_urls]
        chans = clean.dedupe(chans)
        alive = order(test_liveness(chans))
        write_outputs(armor, alive)
    else:
        build.run()


if __name__ == "__main__":
    main()
