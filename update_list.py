#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PuuStream IPTV Motoru — otomatik canlı TV kaynak motoru.

Ne yapar:
  1. GitHub'da güncel Türkçe m3u depolarını arar + sources.txt'deki adresleri tarar
     (doğrudan m3u, GitHub depo/klasör/dosya, gist).
  2. Kanalları temizler, yabancı/VOD/yetişkin/şifreli hesap adreslerini eler.
  3. Aynı kanalın farklı adlarını tek kimlikte toplar (TRT 1 = TRT1 HD = TR: TRT-1).
  4. Her adresi gerçekten test eder: HLS segment içeriği, donma (ilerleme), FFprobe.
  5. Geçmişe göre puanlar, sürekli ölenleri karantinaya alır.
  6. Bozuk güncellemeye karşı korur; tr.m3u + channels.json + health.json + RAPOR.md yazar.

Çalıştırma:
    python update_list.py                 # tam otomasyon
    python update_list.py --no-search     # GitHub araması yok (sources.txt + hafıza)
    python update_list.py --test-only     # kaynak indirme yok: mevcut liste + hafızayı yeniden test et
    python update_list.py --fast          # derin test (FFprobe) ve donma testi kapalı
    python update_list.py --dry-run       # dosya yazmadan dene
    PROBE_REGION=tr python update_list.py --test-only --state-only   # Türkiye'den ikinci doğrulama
    GITHUB_TOKEN=... python update_list.py
"""
import argparse
import logging
import sys


def main():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="PuuStream IPTV motoru")
    ap.add_argument("--test-only", action="store_true", help="kaynak indirme; mevcut liste + hafızayı test et")
    ap.add_argument("--no-search", action="store_true", help="GitHub araması yapma")
    ap.add_argument("--fast", action="store_true", help="FFprobe ve donma testini kapat")
    ap.add_argument("--no-deep", action="store_true", help="yalnızca FFprobe'u kapat")
    ap.add_argument("--max-test", type=int, default=None, help="en fazla test edilecek adres")
    ap.add_argument("--dry-run", action="store_true", help="dosya yazma")
    ap.add_argument("--state-only", action="store_true",
                    help="yalnızca test hafızasını güncelle (Türkiye runner'ı için), liste yayınlama")
    ap.add_argument("--force", action="store_true", help="koruma kontrolünü aş (FORCE_PUBLISH)")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()

    logging.basicConfig(level=logging.DEBUG if a.verbose else logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S")
    logging.getLogger("urllib3").setLevel(logging.ERROR)

    from engine import config as C
    from engine.build import RunOptions, run
    if a.force:
        C.FORCE_PUBLISH = True
    opts = RunOptions(
        search=not (a.no_search or a.test_only),
        fetch_sources=not a.test_only,
        deep=C.DEEP_PROBE and not (a.fast or a.no_deep),
        progress=C.PROGRESS_CHECK and not a.fast,
        max_test=a.max_test or C.MAX_TEST,
        dry_run=a.dry_run,
        state_only=a.state_only,
    )
    _, st = run(opts)
    # koruma devreye girdiyse çıkış kodu 0 kalır (iş akışı kırmızı olmasın), rapor uyarır
    return 0


if __name__ == "__main__":
    sys.exit(main())
