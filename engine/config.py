# -*- coding: utf-8 -*-
"""
Tüm ayarlar burada. Kodun geri kalanına dokunmadan buradan ince ayar yapabilirsin.
Ortam değişkeni (env) ile ezilebilen ayarlar GitHub Actions'tan da değiştirilebilir.
"""
import os
import re as _re


def _env_int(key, default):
    try:
        return int(os.environ.get(key, default))
    except (TypeError, ValueError):
        return default


def _env_bool(key, default):
    v = os.environ.get(key)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "evet", "on")


# ================================================================= dosyalar
TR_FILE       = "tr.m3u"            # klasik oynatıcılar için birleşik liste
ARMOR_FILE    = "zirhli.m3u"        # elle bakımlı kanallar (asla silinmez)
REPORT_FILE   = "RAPOR.md"          # her çalışmada üretilen rapor
SOURCES_FILE  = "sources.txt"       # elle eklenen kaynaklar (m3u / GitHub depo / gist)
CHANNELS_FILE = "channels.json"     # PuuStream: tek kanal + çoklu kaynak
HEALTH_FILE   = "health.json"       # özet sağlık bilgisi (panel/uygulama için)
STATE_DIR     = "state"             # motorun hafızası (geçmiş testler, kaynak puanları)
URL_STATE     = os.path.join(STATE_DIR, "urls.json")
SOURCE_STATE  = os.path.join(STATE_DIR, "sources.json")
LAST_GOOD_DIR = os.path.join(STATE_DIR, "last_good")   # son sağlam yayınlanan çıktılar

# ================================================================= bölge
# Testin yapıldığı yer. GitHub sunucusu = "github". Türkiye'deki self-hosted runner = "tr".
REGION = os.environ.get("PROBE_REGION", "github").strip() or "github"

# ================================================================= performans
THREADS_TEST   = _env_int("THREADS_TEST", 48)     # hızlı test eş zaman
THREADS_FETCH  = _env_int("THREADS_FETCH", 12)    # kaynak indirme eş zaman
THREADS_DEEP   = _env_int("THREADS_DEEP", 8)      # ffprobe eş zaman
HTTP_TIMEOUT   = 12        # kaynak (m3u) indirme zaman aşımı (sn)
TEST_TIMEOUT   = 8         # tek istek zaman aşımı (sn)
MAX_TEST       = _env_int("MAX_TEST", 6000)       # bir çalışmada en fazla kaç adres test edilsin
MAX_SOURCE_BYTES = 15 * 1024 * 1024               # 15 MB'tan büyük m3u indirilmez

# ================================================================= yayın testi
SEGMENT_READ_BYTES = 64 * 1024   # segmentten okunacak bayt
SEGMENT_MINBYTES   = 1880        # gerçek video parçasından en az bu kadar (10 TS paketi)
MANIFEST_MAX_BYTES = 512 * 1024
PROGRESS_CHECK     = _env_bool("PROGRESS_CHECK", True)   # HLS ilerliyor mu (donma testi)
PROGRESS_MIN_WAIT  = 4.0          # ikinci manifest okuması için en az bekleme (sn)
PROGRESS_MAX_WAIT  = 10.0         # en fazla bekleme (sn)
VOD_IS_DEAD        = True         # #EXT-X-ENDLIST olan (bitmiş) yayınlar canlı TV sayılmaz
TLS_PENALTY        = 25           # sertifikası bozuk yayına puan cezası (uygulama açamayabilir)

# Derin test (FFprobe): yalnızca hızlı testi geçen en iyi adaylarda.
DEEP_PROBE         = _env_bool("DEEP_PROBE", True)
DEEP_PER_CHANNEL   = _env_int("DEEP_PER_CHANNEL", 2)     # kanal başına en iyi kaç kaynak
DEEP_MAX           = _env_int("DEEP_MAX", 500)           # bir çalışmada en fazla
DEEP_TIMEOUT       = 20                                  # sn
FFPROBE_BIN        = os.environ.get("FFPROBE_BIN", "ffprobe")

# ================================================================= puanlama / karantina
HISTORY_LEN         = 30      # adres başına saklanan son test sayısı
QUARANTINE_AFTER    = 3       # art arda bu kadar ölü → karantina
QUARANTINE_BASE_H   = 6       # ilk karantina süresi (saat), her seferinde ikiye katlanır
QUARANTINE_MAX_H    = 168     # en fazla 7 gün
FORGET_AFTER_FAILS  = 20      # art arda bu kadar ölü + kaynaklarda artık yok → unut
REMEMBER_OK_DAYS    = 3       # kaynak listesi geçici yoksa bile son X günde sağlam adres tekrar test edilir
GEO_GRACE_HOURS     = 24      # GitHub'dan engelli ama başka bölgede son X saatte sağlam → tut

MAX_SOURCES_PER_CHANNEL = 6   # channels.json'da kanal başına en fazla kaynak
M3U_BACKUPS             = 1   # tr.m3u'da kanal başına en fazla kaç yedek kayıt
MIN_PUBLISH_SCORE       = 35  # bundan düşük puanlı kaynak yayınlanmaz (zırhlılar hariç)

# ================================================================= güvenli yayın (koruma)
GUARD_MIN_CHANNELS   = _env_int("GUARD_MIN_CHANNELS", 40)   # bundan az sağlam kanal → yayınlama
GUARD_MAX_DROP       = 0.35   # önceki yayına göre %35'ten fazla kanal kaybı → yayınlama
GUARD_MIN_FETCH_RATE = 0.25   # kaynakların %25'inden azı indirilebildiyse → yayınlama
FORCE_PUBLISH        = _env_bool("FORCE_PUBLISH", False)

# ================================================================= arama
SEARCH_ENABLED = _env_bool("SEARCH_ENABLED", True)
SEARCH_TERMS = [
    "turkiye iptv", "turkce iptv", "turkiye m3u", "turk tv m3u",
    "trt m3u", "turkiye canli tv", "turkish iptv playlist",
    "iptv turkey", "turkiye kanallar m3u", "canli tv m3u8",
]
TOPIC_SEARCH = ["topic:iptv turkey", "topic:iptv turkiye", "topic:m3u turkey"]
# GitHub kod araması (token gerekir) — taze .m3u dosyaları
CODE_SEARCH_TERMS = ["trt1 extension:m3u", "trt1 extension:m3u8", "\"show tv\" extension:m3u",
                     "atv extension:m3u", "trt spor extension:m3u"]

RECENT_DAYS   = 45
MAX_REPOS     = _env_int("MAX_REPOS", 80)
GITHUB_TOKEN  = (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or "").strip()

# Kaynak karantinası: art arda X çalışmada hiç canlı kanal vermeyen otomatik kaynak bekletilir.
SOURCE_ZERO_YIELD_LIMIT = 4
SOURCE_QUARANTINE_H     = 72

# Her zaman denenecek bilinen açık kaynaklar (sources.txt'e ek olarak).
CURATED_SOURCES = [
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/tr.m3u",
]

# Kanal kimliği zenginleştirme (iptv-org veritabanı: alternatif adlar, logo, tvg-id).
IPTV_ORG_CHANNELS = "https://iptv-org.github.io/api/channels.json"
IPTV_ORG_LOGOS    = "https://iptv-org.github.io/api/logos.json"
ENRICH_ENABLED    = _env_bool("ENRICH_ENABLED", True)

# TV rehberi (XMLTV). tr.m3u başlığına x-tvg-url olarak yazılır. Kendi EPG adresini ekle.
EPG_URLS = [u for u in os.environ.get("EPG_URLS", "").split(",") if u.strip()]

# ================================================================= güvenlik
# Kullanıcı adı/şifre taşıyan adresler (Xtream panelleri, get.php?username=...) otomatik
# toplanan kaynaklardan ALINMAZ ve herkese açık çıktılara yazılmaz.
CRED_QUERY_KEYS = {"username", "password", "user", "pass", "pwd", "passwd"}
CRED_PATH_SKIP  = {"hls", "live", "stream", "streams", "tv", "channel", "channels", "play",
                   "video", "media", "cdn", "content", "out", "v1", "v2", "api", "tr", "iptv", "ch"}

# ================================================================= kalite kapısı
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
VOD_URL_HINTS = ["/movie/", "/movies/", "/series/", "/vod/", "/film/"]

JUNK_NAME_RE = _re.compile(
    r"(svg|xmlns|viewbox|data:|base64|\bhttp\b|%3c|3csvg|</|/>|\bwww\b|\.png|\.jpg|\.svg)",
    _re.I)
MAX_NAME_LEN = 46
MIN_LETTER_RATIO = 0.45

VOD_NAME_RE = _re.compile(r"\b(s\d{1,2}\s?e\d{1,2}|sezon\s?\d|b[öo]l[üu]m\s?\d|\(\d{4}\))\b", _re.I)

TR_HINTS = ("tr", "turk", "türk", "turkiye", "türkiye", "turkey", "trt", "trt1",
            "atv", "show", "fox", "star", "kanal", "beyaz", "tv8", "teve2",
            "bein", "spor", "haber", "ulusal", "yerli")

# ================================================================= isim temizleme
STRIP_TAGS_RE = _re.compile(
    r"\b(FHD|UHD|HD|SD|4K|8K|HEVC|H265|H264|RAW|PLUS|VIP|MOBILE|HQ|LQ|BACKUP|YEDEK\s*\d*|ALT|TEST|"
    r"(?:1080|720|576|480|360|240)P|\d{2,3}FPS|FPS|CANLI|LIVE|"
    r"EUROPE|EURO|\bEUR\b|\bEU\b)\b", _re.I)
# Baştaki ülke/kategori önekleri: "TR:", "TR |", "[TR]", "TR-", "TÜRKİYE:" ...
PREFIX_RE = _re.compile(r"^\s*(?:\|?\s*(?:TR|TUR|TURK|TÜRK|TURKIYE|TÜRKİYE|TURKEY)\s*[:|\-»]+\s*)+", _re.I)
YEDEK_GLUED_RE = _re.compile(r"(YEDEK|BACKUP|ALT)\s*\d*$", _re.I)   # "ATVYEDEK46" → "ATV"
BRACKETS_RE = _re.compile(r"\[.*?\]|\(.*?\)|\{.*?\}")
SITE_RE     = _re.compile(r"\b[\w\-]+\.(com|net|org|tv|site|online|club|info|xyz|me|io|live|stream)\b", _re.I)
SYMBOL_RE   = _re.compile(r"[^\w\sğüşıöçĞÜŞİÖÇ&/+-]", _re.UNICODE)
MULTISPACE_RE = _re.compile(r"\s+")

KEEP_WHOLE = ["trt haber", "trt spor", "trt 1", "trt 2", "a haber", "a spor", "tv 8", "tv8.5"]

# ================================================================= gruplama
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
GROUP_ORDER = ["TR-ULUSAL", "TR-HABER", "TR-SPOR", "TR-ÇOCUK", "TR-BELGESEL", "TR-MÜZİK",
               "TR-DİNİ", "TR-YEREL", DEFAULT_GROUP]
