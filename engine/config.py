# -*- coding: utf-8 -*-
"""
Tüm ayarlar burada. Kodun geri kalanına dokunmadan buradan ince ayar yapabilirsin.
"""
import os

# ----------------------------------------------------------------- dosyalar
TR_FILE      = "tr.m3u"        # üretilen son liste
ARMOR_FILE   = "zirhli.m3u"    # elle bakımlı, ASLA dokunulmayan kanallar (en üste eklenir)
REPORT_FILE  = "RAPOR.md"      # her çalışmada üretilen özet rapor
SOURCES_FILE = "sources.txt"   # elle eklenen ekstra m3u kaynakları (her satır bir URL)

# ----------------------------------------------------------------- performans
THREADS_TEST   = int(os.environ.get("THREADS_TEST", "48"))   # canlılık testi eş zaman
THREADS_FETCH  = int(os.environ.get("THREADS_FETCH", "12"))  # kaynak indirme eş zaman
HTTP_TIMEOUT   = 10        # normal indirme zaman aşımı (sn)
TEST_TIMEOUT   = 7         # tek bir yayını test zaman aşımı (sn)
TEST_RETRY     = 1         # canlılık testinde tekrar sayısı
MAX_TEST       = int(os.environ.get("MAX_TEST", "6000"))     # en fazla kaç aday test edilsin
SEGMENT_MINBYTES = 256     # gerçek video parçasından en az bu kadar bayt gelmeli

# ----------------------------------------------------------------- arama
# GitHub depo araması için terimler. Geniş tutuldu ki saçma değil, isabetli bulsun.
SEARCH_TERMS = [
    "turkiye iptv", "turkce iptv", "turkiye m3u", "turk tv m3u",
    "trt m3u", "turkiye canli tv", "turkish iptv playlist",
    "iptv turkey", "turkiye kanallar m3u",
]
# GitHub kod araması (extension:m3u) için terimler — token varsa çalışır, taze dosya bulur.
CODE_SEARCH_TERMS = ["trt1", "atv", "show tv", "fox", "bein sports turkey", "trt spor"]

RECENT_DAYS   = 45     # yalnızca son X günde güncellenen depolar (tazelik)
MAX_REPOS     = int(os.environ.get("MAX_REPOS", "80"))  # taranacak en fazla depo
GITHUB_TOKEN  = (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or "").strip()

# Her zaman denenecek, bilinen açık kaynaklar (sources.txt'e ek olarak).
CURATED_SOURCES = [
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/tr.m3u",
    "https://iptv-org.github.io/iptv/countries/tr.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/tr_sports.m3u",
]

# ----------------------------------------------------------------- kalite kapısı
# Adı/linki bunları içeren kanallar listeye ALINMAZ (yetişkin, yabancı, VOD, film/dizi).
YASAKLI_SET = {
    # yetişkin
    "adult", "xxx", "+18", "yetişkin", "yetiskin", "porn", "pink", "redlight",
    "playboy", "penthouse", "vivid", "hustler", "erotic", "erotik", "forbidden", "sikis",
    # film / dizi / VOD (canlı TV değil)
    "film", "movie", "movies", "dizi", "diziler", "dizileri", "series", "sinema",
    "vod", "yesilcam", "yeşilçam", "belgesel diziler", "netflix", "exxen", "gain",
    "blutv", "tod original", "disney+", "shahid",
    "s01", "s02", "s03", "s04", "e01", "e02", "e03", "e04", "e05", "sezon",
    # radyo
    "radio", "radyo", " fm", "best fm", "alem fm", "joy turk", "super fm", "power fm",
    # yabancı ülke / yayın
    "persian", "arabic", "polski", "polskie", "bulgaria", "romania", "slovakia",
    "azerbaycan", "azerbeycan", "gledaitv", "glwiz", "mediabay",
    # reklam / panel çöpü
    "7/24", "karaoke", "screen saver", "ss screen", "test kanal",
}

# VOD/film endpoint'i olduğu belli linkleri ele (canlı TV değildir).
VOD_URL_HINTS = ["/movie/", "/movies/", "/series/", "/vod/", "/film/"]

# Kanal adı bu kalıplara UYUYORSA elenir (VOD numaralandırması vb.).
import re as _re
VOD_NAME_RE = _re.compile(r"\b(s\d{1,2}\s?e\d{1,2}|sezon\s?\d|b[öo]l[üu]m\s?\d|\(\d{4}\))\b", _re.I)

# "Canlı TR kanalı mı?" ipuçları — TR önceliklendirme için (eleme değil, sıralama).
TR_HINTS = ("tr", "turk", "türk", "turkiye", "türkiye", "turkey", "trt", "trt1",
            "atv", "show", "fox", "star", "kanal", "beyaz", "tv8", "teve2",
            "bein", "spor", "haber", "ulusal", "yerli")

# ----------------------------------------------------------------- isim temizleme
# Addan sökülecek kalite/bölge/yedek takıları.
STRIP_TAGS_RE = _re.compile(
    r"\b(FHD|UHD|HD|SD|4K|8K|HEVC|H265|H264|RAW|PLUS|VIP|MOBILE|HQ|LQ|BACKUP|YEDEK|ALT|TEST|"
    r"(?:1080|720|576|480|360|240)P|\d{2,3}FPS|FPS|"
    r"EUROPE|EURO|\bEUR\b|\bEU\b)\b", _re.I)
BRACKETS_RE = _re.compile(r"\[.*?\]|\(.*?\)|\{.*?\}")
SITE_RE     = _re.compile(r"\b[\w\-]+\.(com|net|org|tv|site|online|club|info|xyz|me|io|live|stream)\b", _re.I)
SYMBOL_RE   = _re.compile(r"[^\w\sğüşıöçĞÜŞİÖÇ&/+-]", _re.UNICODE)
MULTISPACE_RE = _re.compile(r"\s+")

# Bu isimler bozulmasın diye korunur.
KEEP_WHOLE = ["trt haber", "trt spor", "trt 1", "trt 2", "a haber", "a spor", "tv 8", "tv8.5"]

# ----------------------------------------------------------------- gruplama
GROUP_RULES = [
    ("TR-SPOR",   ["spor", "sport", "bein", "sports", "s sport", "smart", "tivibu spor"]),
    ("TR-HABER",  ["haber", "news", "cnn", "ntv", "a haber", "halk", "sözcü", "tele1", "tgrt"]),
    ("TR-ULUSAL", ["trt", "atv", "show", "fox", "now", "star", "kanal d", "kanal 7", "tv8",
                   "beyaz", "teve2", "360", "tv4", "dmax", "euro"]),
    ("TR-ÇOCUK",  ["çocuk", "cocuk", "kids", "minika", "cartoon", "disney", "nick", "trt çocuk"]),
    ("TR-MÜZİK",  ["müzik", "muzik", "music", "number1", "powertürk", "kral", "dream türk"]),
    ("TR-BELGESEL", ["belgesel", "documentary", "nat geo", "discovery", "dmax", "tlc", "history"]),
]
DEFAULT_GROUP = "TR-DİĞER"
