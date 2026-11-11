# -*- coding: utf-8 -*-
"""Süper bot eklentileri: paralı kanal süzgeci, Yedek= okuma, kardeş sunucular,
resmî sayfa çözücü, kural dışa aktarımı, fork takibi."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine import clean, official, output, parse, siblings, sources  # noqa: E402
from engine import config as C  # noqa: E402
from engine.parse import Channel  # noqa: E402


def test_paid_channels_filtered():
    for n in ["beIN SPORTS 1 HD", "S Sport Plus", "TIVIBU SPOR 2", "Exxen Spor", "SMART SPOR 1",
              "UFC NETWORK", "Baby TV", "Disney Junior", "Cine5", "BEIN MOVIES PREMIERE"]:
        assert clean.is_paid(n), n
    for n in ["TRT 1", "TRT Spor", "A Spor", "NTV", "Tay TV", "TV8,5", "HT Spor", "Show TV",
              "Beyaz TV", "TLC", "DMAX", "FB TV"]:
        assert not clean.is_paid(n), n
    st = {}
    out = clean.refine([Channel("beIN SPORTS 1", "https://x.example/a.m3u8"),
                        Channel("TRT 1", "https://y.example/b.m3u8")], st)
    assert [c.url for c in out] == ["https://y.example/b.m3u8"]
    assert st.get("paid") == 1


def test_yedek_attributes_become_candidates():
    t = ('#EXTM3U\n#EXTINF:-1 group-title="ULUSAL" Yedek="https://b.example/1.m3u8" '
         'Yedek2="https://c.example/2.m3u8" Yedek3="yok",ATV\n'
         '#EXTVLCOPT:http-referrer=https://atv.example/\nhttps://a.example/atv.m3u8\n'
         '#EXTINF:-1,NOW\nhttps://d.example/now.m3u8\n')
    ch = parse.parse(t)
    assert [(c.name, c.url) for c in ch] == [
        ("ATV", "https://a.example/atv.m3u8"), ("ATV", "https://b.example/1.m3u8"),
        ("ATV", "https://c.example/2.m3u8"), ("NOW", "https://d.example/now.m3u8")]
    assert ch[1].headers.get("Referer") == "https://atv.example/"
    assert ch[3].headers == {}


def test_sibling_urls():
    assert siblings.sibling_urls("https://tv-trt1.medya.trt.com.tr/master.m3u8") == [
        "https://tv-trt1.live.trt.com.tr/master.m3u8"]
    assert siblings.sibling_urls("https://tv-trthaber.live.trt.com.tr/master_720.m3u8") == [
        "https://tv-trthaber.medya.trt.com.tr/master_720.m3u8"]
    assert siblings.sibling_urls(
        "https://rnttwmjcin.turknet.ercdn.net/lcpmvefbyo/atv/atv.m3u8?e=1") == [
        "https://trkvz-live.ercdn.net/atv/atv.m3u8"]
    assert siblings.sibling_urls("https://example.com/a.m3u8") == []
    have = {"https://tv-trt1.medya.trt.com.tr/master.m3u8"}
    extra = siblings.expand([Channel("TRT 1", "https://tv-trt1.medya.trt.com.tr/master.m3u8")], have)
    assert [c.url for c in extra] == ["https://tv-trt1.live.trt.com.tr/master.m3u8"]
    assert siblings.expand([Channel("TRT 1", "https://tv-trt1.medya.trt.com.tr/master.m3u8")], have) == []


def test_official_extract_variants():
    d = {"name": "Show TV", "page": "x", "host": "ciner.daioncdn.net", "path": "showtv"}
    esc = r'var u="https:\/\/ciner.daioncdn.net\/showtv\/showtv.m3u8?app=abc&ce=3";'
    assert official.extract(esc, d) == "https://ciner.daioncdn.net/showtv/showtv.m3u8?app=abc&ce=3"
    amp = '<video src="https://ciner.daioncdn.net/showtv/showtv.m3u8?app=1&amp;ce=3">'
    assert official.extract(amp, d) == "https://ciner.daioncdn.net/showtv/showtv.m3u8?app=1&ce=3"
    assert official.extract('<a href="https://ciner.daioncdn.net/haberturktv/h.m3u8">', d) is None
    dflt = {"name": "Beyaz TV", "page": "x"}
    assert official.extract('{"file":"https://b.example/live/x.m3u8"}', dflt) == "https://b.example/live/x.m3u8"
    js = {"name": "A", "page": "x", "json_path": "VideoUrl"}
    assert official.extract('{"VideoUrl":"https:\\/\\/a.example\\/a.m3u8"}', js) == "https://a.example/a.m3u8"
    assert official.extract("", d) is None


def test_official_defs_file_is_valid():
    path = os.path.join(os.path.dirname(__file__), "..", C.OFFICIAL_FILE)
    defs = official.load_defs(path)
    assert len(defs) >= 10
    names = {d["name"] for d in defs}
    assert {"Show TV", "Kanal D", "TV8", "NTV", "Star TV"} <= names
    for d in defs:
        assert d["page"].startswith("https://")


def test_rules_json_roundtrip():
    r = output.rules_json()
    json.dumps(r, ensure_ascii=False)
    assert r["group_order"][0] == "TR-ULUSAL" and r["default_group"] == "TR-DİĞER"
    assert any(g == "TR-HABER" and "haber" in keys for g, keys in r["group_rules"])
    assert r["paid"] == C.PAID_PATTERNS and "ankara" in r["il_adlari"]


def test_top_repos_skips_own_and_radio(monkeypatch):
    monkeypatch.setattr(C, "EXCLUDE_SOURCES", ["me/own"])

    class S:
        data = {
            "https://raw.githubusercontent.com/me/own/main/a.m3u": {"alive": 500},
            "https://raw.githubusercontent.com/x/radio-lists/main/a.m3u": {"alive": 400},
            "https://raw.githubusercontent.com/good/tv/main/a.m3u": {"alive": 50},
            "https://raw.githubusercontent.com/good/tv/main/b.m3u": {"alive": 60},
            "https://raw.githubusercontent.com/ok/list/HEAD/a.m3u": {"alive": 20},
            "https://raw.githubusercontent.com/zero/list/main/a.m3u": {"alive": 0},
        }
    assert sources.top_repos(S(), 5) == [("good", "tv"), ("ok", "list")]


def test_prioritize_gives_every_channel_a_share(monkeypatch):
    from engine import build
    from engine.health import SourceState, UrlState
    monkeypatch.setattr(C, "PER_CHANNEL_TEST", 3)

    class Reg:
        def is_known(self, cid):
            return cid == "trt1"

    cands = []
    for i in range(50):                      # popüler kanalın 50 kopya adresi
        c = Channel("TRT 1", f"https://a.test/trt1/{i}.m3u8"); c.cid = "trt1"; cands.append(c)
    for n in ["Yerel A", "Yerel B", "Yerel C"]:
        c = Channel(n, f"https://b.test/{n}.m3u8"); c.cid = ""; cands.append(c)
    out = build.prioritize(cands, Reg(), UrlState("/nonexistent/u.json"),
                           SourceState("/nonexistent/s.json"), 8)
    names = [c.name for c in out]
    assert len(out) == 8
    assert {"Yerel A", "Yerel B", "Yerel C"} <= set(names)   # eskiden hepsi dışarıda kalırdı
    assert names.count("TRT 1") == 5
