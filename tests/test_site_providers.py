"""Site botları için tamamen çevrimdışı simüle HTML/JSON testleri."""
import base64
import json
from urllib.parse import urlparse

import pytest

from engine.site_providers import collect
from engine.site_providers.common import Page, safe_url, extract_stream
from engine.site_providers import atom, andro, selcuk, xsport, palazzo, zeus, trgoals
from engine.parse import parse, write_m3u


class FakeClient:
    def __init__(self, mapping):
        self.mapping = mapping
        self.requested = []

    def get(self, url, headers=None):
        self.requested.append((url, headers or {}))
        p = self.mapping.get(url)
        if p is None:
            return Page(url, '', 404, {})
        return p if isinstance(p, Page) else Page(url, p, 200, {})


def test_selcuk_player_discovery():
    c = FakeClient({
        'https://sports.test/': '<div data-url="https://sports.test/index.php?id=abc"></div>',
        'https://sports.test/index.php?id=abc': "this.baseStreamUrl='https://cdn.test/live/';",
    })
    out = selcuk.discover(c, {'base_url': 'https://sports.test/', 'channels': {'selcukobs1': 'beIN Sports 1'}})
    assert len(out) == 1
    assert out[0].url == 'https://cdn.test/live/selcukobs1/playlist.m3u8'
    assert out[0].headers['Referer'] == 'https://sports.test/'


def test_atom_fetch_json_and_playback_headers():
    c = FakeClient({
        'https://atom.test/': '<h1>Atom</h1>',
        'https://atom.test/matches?id=trt1': "fetch('/api?id=');",
        'https://atom.test/api?id=trt1': '{"stream":"https://cdn.test/trt1/index.m3u8?quality=high"}',
    })
    out = atom.discover(c, {'base_url': 'https://atom.test/', 'channels': {'trt1':'TRT 1'}})
    assert len(out) == 1
    assert out[0].url.startswith('https://cdn.test/trt1/')
    assert out[0].headers['Origin'] == 'https://atom.test'
    assert c.requested[-1][1]['Referer'] == 'https://atom.test/'


def test_andro_baseurls():
    c = FakeClient({
        'https://andro.test/': 'home',
        'https://andro.test/event.html?id=androstreamlivebs1':
            "const baseurls = ['https://cdn1.test/live', 'https://cdn2.test/checklist'];",
    })
    out = andro.discover(c, {'base_url':'https://andro.test/',
                              'channels':{'androstreamlivebs1':'beIN Sports 1'}})
    assert len(out) == 2
    assert out[0].url == 'https://cdn1.test/live/checklist/androstreamlivebs1.m3u8'
    assert out[1].url == 'https://cdn2.test/checklist/androstreamlivebs1.m3u8'


def test_xsport_per_channel():
    c = FakeClient({
        'https://xsport.test/': '<div data-url="/index.php?id=xssport"></div>',
        'https://xsport.test/index.php?id=xssport':
            "this.baseStreamUrl='https://video.test/live/';",
    })
    out = xsport.discover(c, {'base_url':'https://xsport.test/', 'channels':{'xssport':'S Sport 1'}})
    assert len(out) == 1 and out[0].url.endswith('/xssport/playlist.m3u8')


def test_zeus_static_base():
    c = FakeClient({
        'https://zeus.test/': 'ready',
        'https://zeus.test/ch.html?id=b1': 'var streamUrl = "https://cdn.test/stream/";'
    })
    out = zeus.discover(c, {'base_url':'https://zeus.test/', 'channels':{'b1':'beIN Sports 1'}})
    assert len(out) == 1 and out[0].url == 'https://cdn.test/stream/b1/index.m3u8'


def test_palazzo_plaintext_player():
    c = FakeClient({
        'https://palazzo.test/': '<a href="https://p.test/player2.php?id=">player2.php</a>',
        'https://p.test/player2.php?id=601': '{"url":"https://cdn.test/sp1.m3u8"}'
    })
    out = palazzo.discover(c, {'base_url':'https://palazzo.test/', 'channels':{'601':'beIN Sports 1'}})
    assert len(out) == 1 and out[0].url == 'https://cdn.test/sp1.m3u8'
    assert out[0].headers['Referer'] == 'https://p.test/'


def test_palazzo_aes_html_if_available():
    crypto = pytest.importorskip('Crypto')
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    key = b'0123456789abcdef'
    iv = b'fedcba9876543210'
    offset = 10
    encoded_key = ','.join(str(x+offset) for x in key)
    encoded_iv = base64.b64encode(json.dumps([x+offset for x in iv]).encode()).decode()
    encoded_offset = base64.b64encode(str(offset).encode()).decode()
    stream = 'https://cdn.test/ch.m3u8'
    enc = base64.b64encode(AES.new(key, AES.MODE_CBC, iv).encrypt(pad(stream.encode(),16))).decode()
    raw = (f'<div data-val="{encoded_offset}" data-enc="{encoded_iv}"></div>'
           f'<script>var keyArray=[{encoded_key}];var primaryStream=decryptUrl(\'{enc}\');</script>')
    assert palazzo.decode_public_player(raw, 'https://player.test') == stream


def test_trgoals_configured_static_only():
    out = trgoals.discover(FakeClient({}), {'streams': [{'name':'TRGoals Ana', 'url':'https://cdn.test/live.m3u8'}]})
    assert len(out) == 1 and out[0].source == 'site:trgoals'


def test_all_providers_and_disabled_and_m3u_headers():
    config = {'enabled':True,'providers':{'trgoals':{'enabled':True,'streams':[
        {'name':'TRT Spor','url':'https://cdn.test/trt.m3u8','referer':'https://site.test/'},
    ]}}}
    out = collect(config=config, client=FakeClient({}))
    assert len(out) == 1
    text = write_m3u(out)
    parsed = parse(text)
    assert parsed[0].headers['Referer'] == 'https://site.test/'
    assert not collect(config={'enabled':False,'providers':{}}, client=FakeClient({}))


def test_block_local_urls_and_not_vod():
    for url in ('http://127.0.0.1/a.m3u8','http://localhost/a.m3u8',
                'file:///etc/passwd', 'http://192.168.1.2/live.m3u8',
                'http://user:pass@video.test/live.m3u8'):
        assert not safe_url(url)
    assert extract_stream('{"url":"https://cdn.test/movie.mp4"}', 'https://site.test/') is None
    assert extract_stream('{"url":"https://cdn.test/channel.m3u8"}', 'https://site.test/')


def test_candidates_bounded_and_manual_first():
    from engine.site_providers.common import candidates
    c = {'base_url':'https://manual.test/', 'domain_pattern':'https://domain{n}.test/',
         'auto_domain_scan':True, 'index_start':1,'index_end':4000, 'scan_limit':999}
    urls = candidates(c)
    assert urls[0] == 'https://manual.test/'
    assert len(urls) <= 51
    assert 'https://domain4000.test/' in urls


def test_bayx_gather_integration(monkeypatch, tmp_path):
    from engine import build, identity, sources
    from engine.health import SourceState, UrlState
    cfg = {'enabled': True, 'providers': {'trgoals': {
        'enabled': True, 'streams':[{'name':'TRT Spor','url':'https://cdn.test/live.m3u8',
                                    'referer':'https://site.test/'}]}}}
    from engine import site_providers
    monkeypatch.setattr(site_providers, 'collect', lambda: collect(cfg, client=FakeClient({})))
    monkeypatch.setattr(sources, 'collect_all', lambda **kwargs: [])
    monkeypatch.setattr(build.C, 'SEARCH_ENABLED', False)
    reg = identity.load_registry(None)
    opts = build.RunOptions(fetch_sources=True, fetch_sites=True, search=False, max_test=1)
    stats = build.RunStats()
    pool = build.gather(reg, opts, stats, SourceState(str(tmp_path/'ss.json')),
                        UrlState(str(tmp_path/'us.json')), set())
    assert len(pool) == 1
    assert pool[0].source == 'site:trgoals'
    assert pool[0].headers['Referer'] == 'https://site.test/'
    assert pool[0].cid == 'trtspor'
    assert stats.from_sites == 1
