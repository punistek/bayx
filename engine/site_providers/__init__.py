"""Siteye özel canlı spor keşif modülleri (film/dizi yok).

Şifrelenmiş DRM lisansları, hesap girişleri ve engel aşma yoktur.
Üretilen tüm adaylar mevcut Bayx liveness/guard/health süzgecinden geçer.
"""
import json
import logging
import os
from collections import Counter

from . import selcuk, atom, andro, xsport, palazzo, zeus, trgoals
from .common import Client

log = logging.getLogger('site_providers')
PROVIDERS = {
    'selcuk': selcuk, 'atom': atom, 'andro': andro, 'xsport': xsport,
    'palazzo': palazzo, 'zeus': zeus, 'trgoals': trgoals,
}
DEFAULT_CONFIG = 'site_providers.json'


def load_config(path=None):
    path = path or os.environ.get('SITE_PROVIDERS_CONFIG', DEFAULT_CONFIG)
    try:
        with open(path, encoding='utf-8') as f:
            cfg = json.load(f)
        if not isinstance(cfg, dict) or not isinstance(cfg.get('providers', {}), dict):
            raise ValueError('providers JSON nesnesi bulunamadı')
        return cfg
    except (OSError, ValueError) as exc:
        log.warning('Site yapılandırması okunamadı (%s); site taraması atlandı', type(exc).__name__)
        return {'enabled': False, 'providers': {}}


def collect(config=None, only=None, client=None):
    cfg = config or load_config()
    if not cfg.get('enabled', False):
        log.info('Site keşfi kapalı')
        return []
    client = client or Client(timeout=cfg.get('timeout_seconds', 8))
    out = []
    counts = Counter()
    names = [only] if only else list(PROVIDERS)
    for name in names:
        if name not in PROVIDERS:
            raise ValueError('Bilinmeyen site modülü: ' + str(name))
        opts = (cfg.get('providers') or {}).get(name) or {}
        if not opts.get('enabled', False):
            continue
        try:
            records = PROVIDERS[name].discover(client, opts)
            for ch in records[:200]:
                if ch and ch.url:
                    out.append(ch)
                    counts[name] += 1
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            log.warning('%s keşif hatası: %s', name, type(exc).__name__)
        log.info('%s: %d aday adres', name, counts[name])
    log.info('Site keşif toplamı: %d URL (yayın canlılık testi daha yapılmadı)', len(out))
    return out
