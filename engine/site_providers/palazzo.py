"""Palazzo / Renconnect: HTML player bulur ve sayfanın herkese sunduğu HLS değerini okur.

JS sayfalarının veri-val/data-enc/keyArray/AES-CBC paketlemesi varsa aynı istemci
kodundaki açma işlemi uygulanır. Bu DRM/lisans çözme yöntemi değildir.
"""
import base64
import json
import re
from .common import absolute, active_home, extract_stream, hls_url, item, origin_of, pick, try_get

CHANNELS = {
    '601':'beIN Sports 1', '602':'beIN Sports 2', '603':'beIN Sports 3',
    '604':'beIN Sports 4', '605':'beIN Sports 5',
    '607':'S Sport 1', '608':'S Sport 2', '609':'Smart Spor 1',
    '610':'Smart Spor 2', '701':'Tivibu Spor 1',
    '702':'Tivibu Spor 2', '703':'Tivibu Spor 3',
    '704':'Tivibu Spor 4', 'eurosport1':'Eurosport 1',
    'eurosport2':'Eurosport 2',
}


def decode_public_player(text, base):
    """Player sayfasındaki basit AES-CBC JS paketlemesinden HLS URL'si çıkart."""
    direct = extract_stream(text, base)
    if direct:
        return direct
    val = pick([r'data-val=["\']([^"\']+)["\']'], text)
    iv_enc = pick([r'data-enc=["\']([^"\']+)["\']'], text)
    key_arr = pick([r'\bvar\s+keyArray\s*=\s*\[([^\]]+)\]'], text)
    payload = pick([r'\bvar\s+primaryStream\s*=\s*decryptUrl\(["\']([^"\']+)["\']\)'], text)
    if not (val and iv_enc and key_arr and payload):
        return None
    try:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import unpad
        offset = int(base64.b64decode(val).decode('ascii'))
        iv_nums = json.loads(base64.b64decode(iv_enc))
        key_nums = json.loads('[' + key_arr + ']')
        key = bytes(x - offset for x in key_nums)
        iv = bytes(x - offset for x in iv_nums)
        decoded = unpad(AES.new(key, AES.MODE_CBC, iv).decrypt(base64.b64decode(payload)), 16)
        return hls_url(decoded.decode('utf-8'), base)
    except (ValueError, TypeError, KeyError, ImportError):
        return None


def discover(client, conf):
    home = active_home(client, conf, required=('player2.php', 'primaryStream', 'decryptUrl'))
    if not home:
        return []
    template = pick([r'["\'](https?://[^"\']*player2\.php\?[^"\']*?id=)["\']',
                     r'["\']([^"\']*player2\.php\?[^"\']*?id=)["\']'], home.text)
    if not template:
        return []
    result = []
    for cid, name in (conf.get('channels') or CHANNELS).items():
        player_url = absolute(home.url, template + cid)
        page = try_get(client, player_url, {'Referer': home.url, 'Origin': origin_of(home.url)})
        if not page:
            continue
        stream = decode_public_player(page.text, page.url)
        ch = item('palazzo', name, stream, referer=origin_of(page.url) + '/',
                  origin=origin_of(page.url))
        if ch: result.append(ch)
    return result
