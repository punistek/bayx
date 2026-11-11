# -*- coding: utf-8 -*-
"""Testler dış internete ÇIKMAZ.

Resmî site çözücüleri (official_sources.json) ve famelack gibi gerçek adreslere
giden kaynaklar testlerde kapalıdır. Aksi halde GitHub Actions'ta (internet açık)
bu kaynaklar ekstra aday getirip aday sayısını kontrol eden testleri bozar;
internetsiz ortamda ise geçer — sonuç ortama göre değişmesin.
Bu kaynakları sınayan testler kendi sahte verileriyle çalışır (test_superbot.py).
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine import config as C  # noqa: E402
from engine import extra_sources, official  # noqa: E402


@pytest.fixture(autouse=True)
def _no_external_sources(monkeypatch):
    monkeypatch.setattr(C, "OFFICIAL_ENABLED", False)
    monkeypatch.setattr(C, "FAMELACK_TR", "")
    # Bir test bayrakları açsa bile gerçek ağa gitmesin:
    monkeypatch.setattr(official, "resolve_one", lambda d: None)
    monkeypatch.setattr(extra_sources, "famelack", lambda url=None: [])
