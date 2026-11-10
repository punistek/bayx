#!/usr/bin/env python3
"""Site botlarını, bütün Bayx güncellemesini çalıştırmadan dene.

python site_scan.py --provider atom --output aday_spor.m3u
python site_scan.py --provider all --output aday_spor.m3u

UYARI: Çıktıdaki aday URL'ler canlılık testinden geçmemiştir; yayın amacıyla
kullanmadan önce update_list.py ile test edilmelidir.
"""
import argparse
import logging
from engine.site_providers import PROVIDERS, collect
from engine.parse import write_m3u


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--provider', choices=['all', *PROVIDERS], default='all')
    p.add_argument('--output', default='site_candidates.m3u')
    p.add_argument('--dry-run', action='store_true', help='liste dosyası oluşturma')
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(name)s: %(message)s')
    channels = collect(only=None if args.provider == 'all' else args.provider)
    from collections import Counter
    for site, count in sorted(Counter(c.source for c in channels).items()):
        print(f'{site}: {count} aday')
    print(f'Toplam {len(channels)} aday (henüz sağlık testinden geçmedi)')
    if not args.dry_run:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(write_m3u(channels))
        print(f'Dosya: {args.output}')


if __name__ == '__main__':
    main()
