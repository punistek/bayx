# -*- coding: utf-8 -*-
"""
Bozuk güncellemeye karşı koruma.

Yeni sonuç yayınlanmadan önce kontrol edilir. Şunlardan biri varsa ESKİ sağlam liste korunur:
  - Sağlam kanal sayısı GUARD_MIN_CHANNELS'tan az
  - Önceki yayına göre GUARD_MAX_DROP oranından fazla kanal kaybı
  - Kaynakların çok azı indirilebildi (GitHub/ağ geçici olarak çökmüş)
FORCE_PUBLISH=1 ile koruma bilerek aşılabilir.
"""
import json
import logging
import os

from . import config as C

log = logging.getLogger("guard")
LAST_PUBLISH = os.path.join(C.STATE_DIR, "last_publish.json")


def previous():
    try:
        with open(LAST_PUBLISH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def check(healthy_channels, fetch_ok=None, fetch_total=None):
    """Döndürür: (yayınla_mı, gerekçe)."""
    prev = previous().get("healthy_channels", 0)
    reasons = []
    if healthy_channels < C.GUARD_MIN_CHANNELS:
        reasons.append(f"sağlam kanal çok az ({healthy_channels} < {C.GUARD_MIN_CHANNELS})")
    if prev and healthy_channels < prev * (1 - C.GUARD_MAX_DROP):
        reasons.append(f"aşırı kayıp: {prev} → {healthy_channels} "
                       f"(%{round(100 * (1 - healthy_channels / prev))})")
    if fetch_total and fetch_total >= 4 and fetch_ok / fetch_total < C.GUARD_MIN_FETCH_RATE:
        reasons.append(f"kaynakların çoğu indirilemedi ({fetch_ok}/{fetch_total})")
    if not reasons:
        return True, "kontroller geçti"
    if C.FORCE_PUBLISH:
        log.warning("Koruma uyarısı ama FORCE_PUBLISH açık: %s", "; ".join(reasons))
        return True, "ZORLA yayınlandı: " + "; ".join(reasons)
    log.warning("YAYIN DURDURULDU: %s", "; ".join(reasons))
    return False, "; ".join(reasons)


def remember(stats):
    os.makedirs(C.STATE_DIR, exist_ok=True)
    with open(LAST_PUBLISH, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)
