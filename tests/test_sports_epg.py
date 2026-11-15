# -*- coding: utf-8 -*-
"""Canlı maç bulucu (engine/sports_epg.py) testleri."""
import gzip
import io

from engine import sports_epg as S

NOW = 1794765600  # 15.11.2026 21:00 İstanbul (18:00 UTC)


def _t(h, m=0, day=15):
    return f"202611{day:02d}{h:02d}{m:02d}00 +0300"


XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<tv>
  <channel id="beINSports1.tr"><display-name>beIN SPORTS 1</display-name></channel>
  <channel id="beINSports2.tr"><display-name>beIN SPORTS 2</display-name></channel>
  <channel id="SSport.tr"><display-name>S Sport</display-name></channel>
  <channel id="TRT1.tr"><display-name>TRT 1</display-name></channel>
  <channel id="ATV.tr"><display-name>ATV</display-name></channel>
  <channel id="TV8.tr"><display-name>TV8</display-name></channel>
  <channel id="TRTSpor.tr"><display-name>TRT Spor</display-name></channel>
  <!-- maç: şu an -->
  <programme start="{_t(20)}" stop="{_t(22)}" channel="beINSports1.tr">
    <title>Galatasaray - Fenerbahçe</title><sub-title>Trendyol Süper Lig 12. Hafta</sub-title>
    <category>Futbol</category></programme>
  <!-- yabancı maç, Türk kanalında -->
  <programme start="{_t(21,30)}" stop="{_t(23,30)}" channel="beINSports2.tr">
    <title>Manchester City vs Arsenal (C)</title><desc>Premier League 12. Hafta. Canlı yayın.</desc></programme>
  <!-- basketbol -->
  <programme start="{_t(20,45)}" stop="{_t(22,30)}" channel="SSport.tr">
    <title>Anadolu Efes – Real Madrid</title><category>Basketbol</category></programme>
  <!-- tekrar: elenmeli -->
  <programme start="{_t(18)}" stop="{_t(20)}" channel="beINSports1.tr">
    <title>Beşiktaş - Trabzonspor (Tekrar)</title></programme>
  <!-- özet: elenmeli -->
  <programme start="{_t(22)}" stop="{_t(22,30)}" channel="beINSports1.tr">
    <title>Süper Lig Özetler</title></programme>
  <!-- dizi bölümü, ulusal kanal: elenmeli -->
  <programme start="{_t(20)}" stop="{_t(23)}" channel="ATV.tr">
    <title>Kuruluş Osman - 170. Bölüm</title><category>Dizi</category></programme>
  <!-- ulusal kanalda milli maç (canlı işaretli) -->
  <programme start="{_t(21,45)}" stop="{_t(23,45)}" channel="TRT1.tr">
    <title>Canlı: Türkiye - İspanya</title><sub-title>UEFA Uluslar Ligi</sub-title></programme>
  <!-- ulusal kanalda "A - B" ama spor işareti yok: elenmeli -->
  <programme start="{_t(20)}" stop="{_t(22)}" channel="TV8.tr">
    <title>Gel Konuş - Sonra Gör</title></programme>
  <!-- maç önü: elenmeli -->
  <programme start="{_t(19,30)}" stop="{_t(20)}" channel="TRTSpor.tr">
    <title>Maç Önü</title></programme>
  <!-- canlı ama takım yok, motor sporu -->
  <programme start="{_t(17)}" stop="{_t(19)}" channel="SSport.tr">
    <title>Formula 1 Brezilya GP Canlı</title></programme>
  <!-- yarın akşam: pencere içinde -->
  <programme start="{_t(20,0,16)}" stop="{_t(22,0,16)}" channel="TRTSpor.tr">
    <title>Konyaspor - Sivasspor</title></programme>
  <!-- 3 gün sonra: pencere dışı -->
  <programme start="{_t(20,0,18)}" stop="{_t(22,0,18)}" channel="TRTSpor.tr">
    <title>Kasımpaşa - Alanyaspor</title></programme>
</tv>
"""


def _scan(xml=XML):
    return S.scan_xmltv(io.BytesIO(xml.encode("utf-8")), now=NOW)


def test_time_parse():
    assert S.parse_xmltv_time("20261115210000 +0300") == NOW
    assert S.parse_xmltv_time("20261115180000") == NOW  # bölge yoksa UTC
    assert S.parse_xmltv_time("bozuk") is None


def test_finds_matches_and_filters_noise():
    m = _scan()
    titles = [x["baslik"] for x in m]
    assert "Galatasaray - Fenerbahçe" in titles
    assert "Manchester City vs Arsenal" in titles
    assert "Anadolu Efes – Real Madrid" in titles
    assert "Türkiye - İspanya" in titles
    assert "Formula 1 Brezilya GP" in titles
    assert "Konyaspor - Sivasspor" in titles
    for bad in ("Beşiktaş - Trabzonspor (Tekrar)", "Süper Lig Özetler", "Kuruluş Osman - 170. Bölüm",
                "Gel Konuş - Sonra Gör", "Maç Önü", "Kasımpaşa - Alanyaspor"):
        assert bad not in titles, bad


def test_fields():
    m = {x["baslik"]: x for x in _scan()}
    gs = m["Galatasaray - Fenerbahçe"]
    assert gs["kanal"] == "beIN SPORTS 1" and gs["tvg"] == "beINSports1.tr"
    assert gs["lig"] == "Trendyol Süper Lig 12. Hafta" and gs["tur"] == "futbol"
    assert gs["bas"] <= NOW < gs["bit"]
    assert m["Anadolu Efes – Real Madrid"]["tur"] == "basketbol"
    assert m["Manchester City vs Arsenal"]["canli"] is True
    assert m["Manchester City vs Arsenal"]["lig"] == "Premier League 12"
    assert m["Formula 1 Brezilya GP"]["tur"] == "motor"


def test_gzip_and_dedupe():
    class R:
        status_code = 200

        def __init__(self, b):
            self.b = b

        def raise_for_status(self):
            pass

        def iter_content(self, n):
            yield self.b

    class Sess:
        def get(self, url, **kw):
            return R(gzip.compress(XML.encode("utf-8")))

    # aynı akış iki kez: tekrar eden maç bir kez çıkmalı
    out = S.build(["a.xml.gz", "b.xml.gz"], Sess(), now=NOW)
    assert len(out) == len(_scan())
    assert out == sorted(out, key=lambda x: (x["bas"], x["kanal"].lower()))


def test_build_none_when_all_fail():
    class Bad:
        def get(self, url, **kw):
            raise IOError("yok")

    assert S.build(["x"], Bad(), now=NOW) is None
