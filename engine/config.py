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
MIN_PUBLISH_SCORE       = 35
# zirhli.m3u tr.m3u'ya yazılırken grup adları kendi kategorilerimize çevrilsin mi?
# (Ad, logo, adres, sıra AYNEN kalır; yalnızca "ULUSAL ➤ DİNİ" → "TR-DİNİ" gibi düzeltme.)
ARMOR_NORMALIZE_GROUPS  = True  # bundan düşük puanlı kaynak yayınlanmaz (zırhlılar hariç)

# ================================================================= güvenli yayın (koruma)
GUARD_MIN_CHANNELS   = _env_int("GUARD_MIN_CHANNELS", 40)   # bundan az sağlam kanal → yayınlama
GUARD_MAX_DROP       = 0.35   # önceki yayına göre %35'ten fazla kanal kaybı → yayınlama
GUARD_MIN_FETCH_RATE = 0.25   # kaynakların %25'inden azı indirilebildiyse → yayınlama
FORCE_PUBLISH        = _env_bool("FORCE_PUBLISH", False)

# ================================================================= arama
SEARCH_ENABLED = _env_bool("SEARCH_ENABLED", True)
SEARCH_TERMS = [
    "turkiye iptv", "turkce iptv", "turkiye m3u", "turk tv m3u", "m3u turkiye",
    "trt m3u", "turkiye canli tv", "turkish iptv playlist", "turkish tv m3u8",
    "iptv turkey", "turkiye kanallar m3u", "canli tv m3u8", "tv kanal listesi",
    "turkiye iptv m3u8", "ulusal kanallar m3u", "yerel kanallar m3u", "turk iptv",
    "canli yayin m3u", "iptv tr", "kanal listesi m3u",
]
TOPIC_SEARCH = ["topic:iptv turkey", "topic:iptv turkiye", "topic:m3u turkey"]
# GitHub kod araması (token gerekir) — taze .m3u dosyaları
CODE_SEARCH_TERMS = ["trt1 extension:m3u", "trt1 extension:m3u8", "\"show tv\" extension:m3u",
                     "atv extension:m3u", "trt spor extension:m3u"]

RECENT_DAYS   = 45
MAX_REPOS     = _env_int("MAX_REPOS", 150)
MAX_FILES_PER_REPO = _env_int("MAX_FILES_PER_REPO", 40)   # büyük depolarda TR'ye en yakın N dosya

# Otomatik bulunan dosyalarda yolu yabancı ülke/dil gösterenler indirilmez (ör. /eng/, us.m3u, countries/de.m3u)
FOREIGN_PATH_CODES = set("""us usa uk gb de deu ger fr fra it ita es spa ru rus ua pl ro bg gr nl be pt por
br ar mx in hin ind pk ir fas per iq sa ae eg ma dz tn cn chi zh jp jpn kr kor id my th vn ph ca au mn mon
kz uz af bd lk np sy lb jo kw qa om ye ly sd so et ng gh ke za cl co pe ve ec bo py uy cr pa do cu
hu cz sk si hr rs ba me mk al xk at ch dk se no fi is ie ee lv lt by md ge am il cy mt lu
eng english arabic russian german french spanish italian portuguese hindi chinese korean japanese
indonesia india usa_ latino latam""".split())
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
# Uygulamada görünen kategoriler YALNIZCA bunlar. Kaynaktaki "ULUSAL ➤ DİNİ", "*TÜRK_SPOR",
# "TR-COCUK" gibi tüm grup adları bu listeye çevrilir.
G_ULUSAL, G_HABER, G_SPOR = "TR-ULUSAL", "TR-HABER", "TR-SPOR"
G_COCUK, G_BELGESEL, G_MUZIK = "TR-ÇOCUK", "TR-BELGESEL", "TR-MÜZİK"
G_DINI, G_YEREL, G_SINEMA, G_DIZI = "TR-DİNİ", "TR-YEREL", "TR-SİNEMA", "TR-DİZİ"
DEFAULT_GROUP = "TR-DİĞER"
GROUP_ORDER = [G_ULUSAL, G_HABER, G_SPOR, G_COCUK, G_BELGESEL, G_MUZIK, G_DINI,
               G_SINEMA, G_DIZI, G_YEREL, DEFAULT_GROUP]

# Anahtar kelime → kategori. SIRA ÖNEMLİ: ilk eşleşen kazanır (ör. "ULUSAL ➤ DİNİ" → DİNİ).
# Kelimeler Türkçe karaktersiz ve küçük harfle yazılır.
GROUP_RULES = [
    (G_COCUK,    ["cocuk", "kids", "kid", "minika", "cartoon", "disney", "nick", "baby", "spacetoon",
                  "eba", "trt genc", "cizgi", "pepee"]),
    (G_DINI,     ["dini", "diyanet", "semerkand", "lalegul", "kuran", "quran", "islam", "mekke",
                  "medine", "makkah", "madinah", "hilal", "rehber tv", "dost tv", "kanal 24 dini",
                  "berat", "vav tv", "mesaj tv", "ilahi"]),
    (G_SPOR,     ["spor", "sport", "bein", "s sport", "tjk", "tay tv", "fb tv", "gs tv", "bjk tv",
                  "trabzonspor", "nba", "eurosport", "tivibu spor", "smart spor", "exxen spor", "derbi"]),
    (G_HABER,    ["haber", "news", "cnn", "ntv", "halk tv", "sozcu", "tele1", "tgrt", "bloomberg",
                  "ekonomi", "finans", "cnbc", "ekotur", "tv100", "tvnet", "ulke tv", "akit", "tbmm",
                  "a para", "bengu"]),
    (G_BELGESEL, ["belgesel", "documentary", "nat geo", "national geographic", "discovery", "dmax",
                  "tlc", "history", "animal", "ciftci", "yaban", "av tv", "gezi", "viasat"]),
    (G_MUZIK,    ["muzik", "music", "kral", "power", "number1", "number one", "dream turk", "nr1",
                  "slow", "akustik", "taptaze", "damar", "arabesk", "turku", "pop tv", "rap"]),
    (G_SINEMA,   ["sinema", "film", "movie", "cine", "yesilcam"]),
    (G_DIZI,     ["dizi", "series"]),
    (G_YEREL,    ["yerel", "kent", "belediye", "bolge", "karadeniz", "ege", "akdeniz", "guneydogu",
                  "dogu", "anadolu", "postasi", "diyar", "hunat", "ruha", "sunrtv", "sun rtv", "kay tv",
                  "kaytv", "mercan", "frt", "cem tv", "brt", "ktv", "tontv", "ton tv"]),
    (G_ULUSAL,   ["ulusal", "national", "trt", "atv", "show", "fox", "star", "kanal d", "kanal 7",
                  "tv8", "tv 8", "beyaz", "teve2", "360", "tv4", "a2", "now", "tabii", "tv 24"]),
]

# Türkiye il adları → TR-YEREL (ör. "ORDU TV", "KANAL 23 ELAZIĞ", "MALATYA VUSLAT")
IL_ADLARI = """adana adiyaman afyon agri amasya ankara antalya artvin aydin balikesir bilecik bingol
bitlis bolu burdur bursa canakkale cankiri corum denizli diyarbakir edirne elazig erzincan erzurum
eskisehir gaziantep antep giresun gumushane hakkari hatay isparta mersin icel istanbul izmir kars
kastamonu kayseri kirklareli kirsehir kocaeli konya kutahya malatya manisa kahramanmaras maras mardin
mugla mus nevsehir nigde ordu rize sakarya samsun siirt sinop sivas tekirdag tokat trabzon tunceli
sanliurfa urfa usak van yozgat zonguldak aksaray bayburt karaman kirikkale batman sirnak bartin
ardahan igdir yalova karabuk kilis osmaniye duzce alanya bodrum marmaris fethiye iskenderun
tarsus edessa erciyes""".split()
# "Kanal 23", "TV 52", "TV41" gibi plaka numaralı kanallar → TR-YEREL
PLAKA_RE = _re.compile(r"\b(?:kanal|tv)\s?(1\d|[2-7]\d|8[01])\b", _re.I)
