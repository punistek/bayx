# -*- coding: utf-8 -*-
"""Testler için sahte yayın sunucusu: canlı, donmuş, VOD, sahte segment, HTML, 403, DRM..."""
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
AV = open(os.path.join(HERE, "seg_av.ts"), "rb").read()
AUDIO = open(os.path.join(HERE, "seg_audio.ts"), "rb").read()
T0 = time.time()


def media_playlist(seq, segpath, n=4, ended=False, key=""):
    out = ["#EXTM3U", "#EXT-X-VERSION:3", "#EXT-X-TARGETDURATION:1", f"#EXT-X-MEDIA-SEQUENCE:{seq}"]
    if key:
        out.append(key)
    for i in range(seq, seq + n):
        out += ["#EXTINF:1.0,", f"{segpath}/{i}.ts"]
    if ended:
        out.append("#EXT-X-ENDLIST")
    return "\n".join(out) + "\n"


MASTER = """#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360,CODECS="avc1.42e01e,mp4a.40.2"
360/index.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=2500000,RESOLUTION=1280x720,CODECS="avc1.64001f,mp4a.40.2"
720/index.m3u8
"""

M3U_SOURCE = """#EXTM3U
#EXTINF:-1 tvg-id="TRT1.tr" tvg-logo="http://logo/trt1.png" group-title="Ulusal",TRT 1 HD
{B}/live/master.m3u8
#EXTINF:-1 group-title="Ulusal",TR: TRT1 FHD
{B}/live2/index.m3u8
#EXTINF:-1,TRT-1 (Yedek)
{B}/frozen/index.m3u8
#EXTINF:-1,Show TV
#EXTVLCOPT:http-referrer=https://www.showtv.com.tr/
{B}/needref/index.m3u8
#EXTINF:-1,SHOW HD
{B}/fake/index.m3u8
#EXTINF:-1,Kanal D
{B}/direct.ts
#EXTINF:-1,Halk TV
{B}/html/index.m3u8
#EXTINF:-1,NTV
{B}/vod/index.m3u8
#EXTINF:-1,Habertürk
{B}/blocked/index.m3u8
#EXTINF:-1,TV8
{B}/drm/index.m3u8
#EXTINF:-1,Fox News Channel
{B}/live3/index.m3u8
#EXTINF:-1,Panel Kanal
http://panel.example:8080/kullanici/sifre/12345
#EXTINF:-1,Get Php
http://panel.example/get.php?username=a&password=b&type=m3u
#EXTINF:-1,Yerel Haber Medya
{B}/live4/index.m3u8
#EXTINF:-1,Kral Radyo FM
{B}/live5/index.m3u8
"""


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ct="application/vnd.apple.mpegurl"):
        if isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        p = self.path.split("?")[0]
        live_seq = int(time.time() - T0) + 100
        base = f"http://{self.headers.get('Host')}"
        if p == "/source.m3u":
            return self._send(200, M3U_SOURCE.replace("{B}", base), "text/plain")
        if p == "/live/master.m3u8":
            return self._send(200, MASTER)
        if p.startswith(("/live/", "/live2/", "/live3/", "/live4/", "/live5/")) and p.endswith("index.m3u8"):
            return self._send(200, media_playlist(live_seq, "seg"))
        if p == "/needref/index.m3u8":
            if "showtv" not in (self.headers.get("Referer") or ""):
                return self._send(403, "<html>Forbidden</html>", "text/html")
            return self._send(200, media_playlist(live_seq, "seg"))
        if "/seg/" in p and p.endswith(".ts"):
            return self._send(200, AV, "video/mp2t")
        if p.startswith("/audio/") and p.endswith("index.m3u8"):
            return self._send(200, media_playlist(live_seq, "aseg"))
        if "/aseg/" in p:
            return self._send(200, AUDIO, "video/mp2t")
        if p == "/frozen/index.m3u8":
            return self._send(200, media_playlist(5, "seg"))
        if p == "/vod/index.m3u8":
            return self._send(200, media_playlist(0, "seg", ended=True))
        if p == "/fake/index.m3u8":
            return self._send(200, media_playlist(live_seq, "bad"))
        if "/bad/" in p:
            return self._send(200, "<html><body>Error: token expired</body></html>" * 60, "text/html")
        if p == "/html/index.m3u8":
            return self._send(200, "<!doctype html><html>Yayın yok</html>", "text/html")
        if p == "/blocked/index.m3u8":
            return self._send(403, "geo blocked", "text/plain")
        if p == "/drm/index.m3u8":
            return self._send(200, media_playlist(live_seq, "seg", key='#EXT-X-KEY:METHOD=SAMPLE-AES,URI="skd://x",KEYFORMAT="com.apple.streamingkeydelivery"'))
        if p == "/direct.ts":
            return self._send(200, AV, "video/mp2t")
        return self._send(404, "not found", "text/plain")


def start():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"
