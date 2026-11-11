"""Çalışma zaman bütçesi.

GitHub işi `timeout-minutes` dolunca öldürülür ve o ana kadarki tüm emek kaybolur
(liste de hafıza da kaydedilmez). Motor bu yüzden kendi saatini tutar; her aşama
kalan süreye bakar, bütçe dolunca elindekiyle yetinip listeyi yazar.
"""
import time

from . import config as C

_t0 = time.time()


def start():
    global _t0
    _t0 = time.time()


def elapsed():
    return time.time() - _t0


def deadline():
    """Tüm çalışmanın bitmesi gereken an (epoch sn)."""
    return _t0 + C.RUN_BUDGET_MIN * 60


def left():
    return deadline() - time.time()
