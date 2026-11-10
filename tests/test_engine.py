# -*- coding: utf-8 -*-
"""Motor testleri. Çalıştır:  python -m pytest -q"""
import json
import os
import shutil
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("NO_PROXY", "127.0.0.1,localhost")
os.environ["no_proxy"] = os.environ["NO_PROXY"]

from engine import config as C  # noqa: E402
from engine import clean, guard, identity, liveness  # noqa: E402
from engine.parse import Channel, parse  # noqa: E402

C.PROGRESS_MIN_WAIT = 1.6
C.TEST_TIMEOUT = 4


@pytest.fixture(scope="module")
def server():
    import mock_server
    srv, base = mock_server.start()
    yield base
    srv.shutdown()


# ------------------------------------------------------------------ yayın testi
def test_live_hls_master_picks_720_and_progresses(server):
    p = liveness.probe(server + "/live/master.m3u8")
    assert p.status == "ok", p.reason
    assert p.kind == "hls" and p.height == 720
    liveness.recheck(p)
    assert p.progress is True and p.status == "ok"


def test_frozen_stream_detected(server):
    p = liveness.probe(server + "/frozen/index.m3u8")
    assert p.status == "ok"
    liveness.recheck(p)
    assert p.progress is False and p.status == "unstable"


def test_vod_is_dead(server):
    p = liveness.probe(server + "/vod/index.m3u8")
    assert p.status == "dead" and "vod" in p.reason


def test_fake_segment_is_dead(server):
    p = liveness.probe(server + "/fake/index.m3u8")
    assert p.status == "dead" and "segment" in p.reason


def test_html_page_is_dead(server):
    assert liveness.probe(server + "/html/index.m3u8").status == "dead"


def test_blocked_is_not_dead(server):
    assert liveness.probe(server + "/blocked/index.m3u8").status == "blocked"


def test_drm_is_dead(server):
    p = liveness.probe(server + "/drm/index.m3u8")
    assert p.status == "dead" and p.reason == "drm"


def test_direct_ts(server):
    p = liveness.probe(server + "/direct.ts")
    assert p.status == "ok" and p.kind == "ts"


def test_headers_are_used(server):
    assert liveness.probe(server + "/needref/index.m3u8").status == "blocked"
    p = liveness.probe(server + "/needref/index.m3u8", {"Referer": "https://www.showtv.com.tr/"})
    assert p.status == "ok"


def test_404_dead(server):
    assert liveness.probe(server + "/yok.m3u8").status == "dead"


@pytest.mark.skipif(not shutil.which("ffprobe"), reason="ffprobe yok")
def test_ffprobe_video_and_audio(server):
    p = liveness.probe(server + "/direct.ts")
    liveness.deep_probe(p)
    assert p.deep and p.has_video and p.has_audio and p.vcodec == "h264" and p.height == 360


@pytest.mark.skipif(not shutil.which("ffprobe"), reason="ffprobe yok")
def test_ffprobe_audio_only_is_unstable(server):
    p = liveness.probe(server + "/audio/index.m3u8")
    assert p.status == "ok"
    liveness.deep_probe(p)
    assert p.has_video is False and p.status == "unstable"


def test_ts_byte_checks():
    assert liveness.media_bytes_ok(bytes([0x47] + [0] * 187) * 20)
    assert not liveness.media_bytes_ok(b"<html>" + b"x" * 5000)
    assert not liveness.media_bytes_ok(b"\x47" * 100)


# ------------------------------------------------------------------ kimlik
@pytest.mark.parametrize("name,cid", [
    ("TRT 1", "trt1"), ("TRT1 HD", "trt1"), ("TR: TRT-1 FHD", "trt1"), ("[TR] TRT 1 1080P", "trt1"),
    ("TRT1YEDEK3", "trt1"), ("ATVYEDEK46", "atv"), ("Show TV", "showtv"), ("SHOW HD", "showtv"),
    ("FOX TV", "now"), ("NOW", "now"), ("Halk", "halktv"), ("Halk TV Canlı", "halktv"),
    ("Habertürk", "haberturk"), ("HABERTURK TV", "haberturk"), ("TV 8,5", "tv85"),
    ("TRT Spor Yıldız", "trtsporyildiz"), ("Kanal D (Yedek)", "kanald"), ("KANALDYEDEK40", "kanald"),
    ("Show Max", "showmax"), ("Kanal 7 Avrupa", "kanal7avrupa"),
])
def test_identity(name, cid):
    reg = identity.Registry()
    c = Channel(name=clean.clean_name(name), url="http://x/y.m3u8")
    c.raw_name = name
    assert reg.resolve(c, source_is_tr=True)[0] == cid      # Türk listesinden gelen kayıt


@pytest.mark.parametrize("name,tvg,url,source,expect", [
    ("NTV", "NTV.ru", "http://x/ntv.m3u8", "http://a/tr.m3u", None),           # Rus NTV
    ("NTV", "", "http://x/ntv.m3u8", "http://a/playlists/mon/general.m3u", None),  # Moğol listesi
    ("NTV", "", "https://ntv.daioncdn.net/ntv/ntv.m3u8", "http://a/list.m3u", "ntv"),  # Türk CDN
    ("NTV", "NTV.tr", "http://x/ntv.m3u8", "http://a/list.m3u", "ntv"),         # .tr tvg-id
    ("Bloomberg", "", "http://x/b.m3u8", "http://a/eng/business.m3u", None),
    ("ATV", "", "http://x/a.m3u8", "http://a/turkiye/kanallar.m3u", "atv"),    # Türk kaynak yolu
    ("TRT 1", "", "http://x/t.m3u8", "http://a/list.m3u", "trt1"),             # tek anlamlı ad
    ("Kanal D", "KanalD.ro", "http://x/k.m3u8", "http://a/tr.m3u", None),      # Romanya Kanal D
])
def test_identity_foreign_safe(name, tvg, url, source, expect):
    reg = identity.Registry()
    c = Channel(name=clean.clean_name(name), url=url, tvg_id=tvg, source=source)
    c.raw_name = name
    cid, known = reg.resolve(c)
    assert (cid if known else None) == expect


@pytest.mark.parametrize("grp,expect", [
    ("ULUSAL ? DİNİ", "TR-DİNİ"), ("*TÜRK_SPOR", "TR-SPOR"), ("TR-COCUK", "TR-ÇOCUK"),
    ("TR-SINEMA", "TR-SİNEMA"), ("??BEİNSPORTS DERBİ ÖZEL??", "TR-SPOR"), ("ULUSAL ? HABER", "TR-HABER"),
    ("TR-MUZIK", "TR-MÜZİK"), ("Yerel", "TR-YEREL"), ("TR-DIZI", "TR-DİZİ"), ("ULUSAL", "TR-ULUSAL"),
])
def test_group_normalize(grp, expect):
    assert clean.normalize_group(grp) == expect


@pytest.mark.parametrize("name,expect", [
    ("KANAL 23 ELAZIG", "TR-YEREL"), ("TV52 ORDU", "TR-YEREL"), ("ERCIYES TV", "TR-YEREL"),
    ("POWERTURK AKUSTIK", "TR-MÜZİK"), ("SEMERKAND TV", "TR-DİNİ"), ("TRT EBA LISE", "TR-ÇOCUK"),
])
def test_group_from_name(name, expect):
    c = Channel(name=name, url="x")
    assert clean.assign_group(c) == expect


def test_foreign_filtered():
    reg = identity.Registry()
    for nm, expect in [("Fox News Channel", False), ("Star Maa", False), ("Yerel Haber", True),
                       ("Çorum Kent", True)]:
        c = Channel(name=clean.clean_name(nm), url="http://x", source="http://other/list.m3u")
        c.raw_name = nm
        cid, known = reg.resolve(c)
        assert reg.tr_relevant(c, known) is expect, nm


# ------------------------------------------------------------------ güvenlik
@pytest.mark.parametrize("url,cred", [
    ("http://190502.tomtv.eu:80/abc/def/61351", True),
    ("http://x.com:8080/live/user/pass/12.ts", True),
    ("http://x.com/get.php?username=a&password=b", True),
    ("http://user:pw@x.com/stream.m3u8", True),
    ("https://tv8.daioncdn.net/tv8/tv8.m3u8", False),
    ("https://cdn.x/hls/live/12345", False),
    ("https://demiroren.daioncdn.net/kanald/kanald.m3u8?app=da2109ea", False),
])
def test_credentials(url, cred):
    assert clean.has_credentials(url) is cred


def test_parse_headers_roundtrip():
    txt = ('#EXTM3U\n#EXTINF:-1 tvg-id="a",A\n#EXTVLCOPT:http-user-agent=UA1\n'
           '#EXTHTTP:{"Referer":"https://r/"}\nhttps://s/a.m3u8|Origin=https://o\n')
    c = parse(txt)[0]
    assert c.headers == {"User-Agent": "UA1", "Referer": "https://r/", "Origin": "https://o"}
    assert c.url == "https://s/a.m3u8"
    out = c.to_m3u()
    assert "http-referrer=https://r/" in out and "http-origin=https://o" in out


# ------------------------------------------------------------------ koruma
def test_guard(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(guard, "LAST_PUBLISH", str(tmp_path / "lp.json"))
    monkeypatch.setattr(C, "GUARD_MIN_CHANNELS", 10)
    assert guard.check(5)[0] is False
    assert guard.check(100)[0] is True
    guard.remember({"healthy_channels": 100})
    assert guard.check(60)[0] is False          # %40 kayıp
    assert guard.check(80)[0] is True
    assert guard.check(80, 1, 10)[0] is False   # kaynakların çoğu inmedi


# ------------------------------------------------------------------ uçtan uca
def test_end_to_end(server, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "sources.txt").write_text(f"# test\n{server}/source.m3u\n", encoding="utf-8")
    (tmp_path / "zirhli.m3u").write_text(
        "#EXTM3U\n#EXTINF:-1,ATVYEDEK1\n" + server + "/live/720/index.m3u8\n"
        "#EXTINF:-1,KANALDYEDEK9\n" + server + "/vod/index.m3u8\n"
        "#EXTINF:-1,HALKTVYEDEK2\n" + server + "/html/index.m3u8\n", encoding="utf-8")
    monkeypatch.setattr(C, "CURATED_SOURCES", [])
    monkeypatch.setattr(C, "GUARD_MIN_CHANNELS", 2)
    monkeypatch.setattr(guard, "LAST_PUBLISH", str(tmp_path / "state" / "last_publish.json"))
    from engine import build
    opts = build.RunOptions(search=False, deep=bool(shutil.which("ffprobe")), progress=True)
    channels, st = build.run(opts)

    data = json.loads((tmp_path / "channels.json").read_text(encoding="utf-8"))
    byid = {c["id"]: c for c in data["channels"]}
    # TRT 1: 3 farklı ad → tek kanal; donmuş kaynak sonda ve 'unstable'
    trt = byid["trt1"]
    assert trt["name"] == "TRT 1" and trt["status"] == "ok"
    st_list = [s["status"] for s in trt["sources"]]
    assert st_list[:2] == ["ok", "ok"] and "unstable" in st_list
    assert trt["sources"][0]["score"] >= trt["sources"][-1]["score"]
    # Show TV: referer başlığıyla çalışan kaynak var, sahte segmentli düştü
    show = byid["showtv"]
    assert len(show["sources"]) == 1 and show["sources"][0]["headers"]["Referer"]
    # Kanal D: zırhlı adres ölü (vod) ama otomatik kaynak (direct.ts) ile kurtarıldı
    kd = byid["kanald"]
    assert kd["armored"] and kd["status"] == "ok"
    assert kd["sources"][0]["armored"] is False and kd["sources"][-1]["armored"] is True
    # Halk TV: zırhlı, tamamen ölü ama SİLİNMEDİ
    assert byid["halktv"]["armored"] and byid["halktv"]["status"] == "dead"
    # elenenler
    assert "x-foxnewschannel" not in byid and "ntv" not in byid and "tv8" not in byid
    assert st.filtered["credential"] == 2
    assert not any("panel.example" in s["url"] for c in data["channels"] for s in c["sources"])
    # zırhlı sıra korunur ve en üstte
    assert [c["id"] for c in data["channels"][:3]] == ["atv", "kanald", "halktv"]
    # tr.m3u: zırhlı blok birebir + otomatik bölüm
    m3u = (tmp_path / "tr.m3u").read_text(encoding="utf-8")
    assert ",ATVYEDEK1\n" in m3u and ",KANALDYEDEK9\n" in m3u          # zırhlı adlar aynen
    assert 'group-title="TR-ULUSAL",ATVYEDEK1' in m3u                    # grup düzeltilmiş
    assert m3u.index("ATVYEDEK1") < m3u.index("KANALDYEDEK9") < m3u.index("HALKTVYEDEK2")  # sıra aynen
    assert "Kanal D (Otomatik)" in m3u and "TRT 1 (Yedek 1)" in m3u
    assert "panel.example" not in m3u
    health = json.loads((tmp_path / "health.json").read_text(encoding="utf-8"))
    assert health["published"] and health["armored"]["rescued_by_auto"] == 1
    assert (tmp_path / "state" / "urls.json").exists()
    assert "Zırhlı kanallar" in (tmp_path / "RAPOR.md").read_text(encoding="utf-8")

    # 2. tur: kaynak listesi erişilemez → hafızadan geri çağrılır, liste korunur
    (tmp_path / "sources.txt").write_text(f"{server}/yok.m3u\n", encoding="utf-8")
    channels2, st2 = build.run(opts)
    assert st2.from_memory > 0
    data2 = json.loads((tmp_path / "channels.json").read_text(encoding="utf-8"))
    assert {c["id"] for c in data2["channels"]} >= {"trt1", "showtv", "kanald"}


def test_guard_protects_memory(server, tmp_path, monkeypatch):
    """Her şey ölü görünürse (ağ arızası) ne liste ne hafıza bozulur."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "sources.txt").write_text(f"{server}/source.m3u\n", encoding="utf-8")
    monkeypatch.setattr(C, "CURATED_SOURCES", [])
    monkeypatch.setattr(C, "GUARD_MIN_CHANNELS", 2)
    monkeypatch.setattr(guard, "LAST_PUBLISH", str(tmp_path / "state" / "last_publish.json"))
    from engine import build
    opts = build.RunOptions(search=False, deep=False, progress=False)
    build.run(opts)
    before_m3u = (tmp_path / "tr.m3u").read_text(encoding="utf-8")
    before_state = (tmp_path / "state" / "urls.json").read_text(encoding="utf-8")
    monkeypatch.setattr(liveness, "probe", lambda url, headers=None, retries=1:
                        liveness.Probe(url=url, status="dead", reason="timeout"))
    _, st = build.run(opts)
    assert st.publish is False
    assert (tmp_path / "tr.m3u").read_text(encoding="utf-8") == before_m3u
    assert (tmp_path / "state" / "urls.json").read_text(encoding="utf-8") == before_state
    assert "DURDURULDU" in (tmp_path / "RAPOR.md").read_text(encoding="utf-8")
