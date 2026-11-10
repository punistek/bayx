# -*- coding: utf-8 -*-
"""
Kanal kimliği: "TRT 1", "TRT1 HD", "TR: TRT-1 FHD", "TRT1YEDEK3" → tek kimlik: trt1

1. İsim temizlenir (önek, kalite takısı, YEDEK numarası atılır) ve sade anahtara çevrilir.
2. Yerleşik katalogda (aşağıda) karşılığı aranır → doğru ad, grup, sıra.
3. iptv-org veritabanı erişilebilirse alternatif adlar, tvg-id ve logo ile zenginleştirilir.
4. Katalogda yoksa anahtarın kendisi kimlik olur ("x-" önekiyle).
"""
import logging
import re

from . import config as C
from .clean import clean_name, fold

log = logging.getLogger("identity")

# (kimlik, görünen ad, grup, [ek takma adlar])  — sıra = listede gösterim sırası
CATALOG = [
    # ---------------------------------------------------------------- ulusal
    ("trt1", "TRT 1", "TR-ULUSAL", ["trt", "trt bir", "trt1 tr"]),
    ("atv", "ATV", "TR-ULUSAL", ["atv turkiye", "a tv"]),
    ("kanald", "Kanal D", "TR-ULUSAL", ["kanal d turkiye"]),
    ("showtv", "Show TV", "TR-ULUSAL", ["show"]),
    ("startv", "Star TV", "TR-ULUSAL", ["star"]),
    ("now", "NOW", "TR-ULUSAL", ["now tv", "fox", "fox tv", "fox turkiye", "now turkiye"]),
    ("tv8", "TV8", "TR-ULUSAL", ["tv 8"]),
    ("kanal7", "Kanal 7", "TR-ULUSAL", []),
    ("beyaztv", "Beyaz TV", "TR-ULUSAL", []),
    ("tv360", "360", "TR-ULUSAL", ["360 tv", "tv 360"]),
    ("teve2", "Teve2", "TR-ULUSAL", ["tv2", "teve 2"]),
    ("tv85", "TV8,5", "TR-ULUSAL", ["tv8 5", "tv 8 5", "tv8.5", "tv8 bucuk"]),
    ("tv4", "TV4", "TR-ULUSAL", ["tv 4"]),
    ("a2", "A2", "TR-ULUSAL", ["a2 tv"]),
    ("trt2", "TRT 2", "TR-ULUSAL", []),
    ("trtturk", "TRT Türk", "TR-ULUSAL", ["trt turk"]),
    ("trtavaz", "TRT Avaz", "TR-ULUSAL", []),
    ("trtkurdi", "TRT Kurdî", "TR-ULUSAL", ["trt kurdi", "trt 6"]),
    ("trtarabi", "TRT Arabi", "TR-ULUSAL", []),
    ("trtworld", "TRT World", "TR-HABER", []),
    ("showmax", "Show Max", "TR-ULUSAL", []),
    ("showturk", "Show Türk", "TR-ULUSAL", []),
    ("kanal7avrupa", "Kanal 7 Avrupa", "TR-ULUSAL", []),
    ("eurod", "Euro D", "TR-ULUSAL", []),
    ("eurostar", "Euro Star", "TR-ULUSAL", []),
    ("tabiitv", "tabii TV", "TR-ULUSAL", ["tabii"]),
    ("dmax", "DMAX", "TR-BELGESEL", []),
    ("tlc", "TLC", "TR-BELGESEL", ["tlc tv"]),
    ("tv24", "TV 24", "TR-ULUSAL", ["24 tv", "24"]),
    ("flashtv", "Flash TV", "TR-ULUSAL", []),
    ("bengutv", "Bengütürk", "TR-ULUSAL", ["benguturk", "benguturk tv"]),
    ("tytturk", "TYT Türk", "TR-ULUSAL", []),
    ("kanalb", "Kanal B", "TR-ULUSAL", []),
    ("tvnet", "TVNET", "TR-HABER", []),
    ("ulketv", "Ülke TV", "TR-HABER", []),
    ("lalegultv", "Lalegül TV", "TR-DİNİ", []),
    ("semerkandtv", "Semerkand TV", "TR-DİNİ", []),
    ("diyanettv", "Diyanet TV", "TR-DİNİ", []),
    ("vavtv", "Vav TV", "TR-ULUSAL", []),
    ("tbmmtv", "TBMM TV", "TR-HABER", []),
    ("tivi6", "Tivi6", "TR-ULUSAL", []),
    ("meltemtv", "Meltem TV", "TR-ULUSAL", []),
    ("cifcitv", "Çiftçi TV", "TR-BELGESEL", ["ciftci tv"]),
    ("birtv", "Bir TV", "TR-ULUSAL", []),
    ("tontv", "Ton TV", "TR-ULUSAL", []),
    ("gzttv", "GZT TV", "TR-HABER", []),
    ("tjktv", "TJK TV", "TR-SPOR", []),
    ("caytv", "Çay TV", "TR-YEREL", []),
    ("aksutv", "Aksu TV", "TR-YEREL", []),
    ("kocaelitv", "Kocaeli TV", "TR-YEREL", []),
    # ---------------------------------------------------------------- haber
    ("ahaber", "A Haber", "TR-HABER", []),
    ("trthaber", "TRT Haber", "TR-HABER", []),
    ("cnnturk", "CNN Türk", "TR-HABER", ["cnn turk"]),
    ("ntv", "NTV", "TR-HABER", []),
    ("haberturk", "Habertürk", "TR-HABER", ["haberturk tv", "ht"]),
    ("halktv", "Halk TV", "TR-HABER", ["halk"]),
    ("sozcutv", "Sözcü TV", "TR-HABER", ["sozcu", "sozcu tv"]),
    ("tele1", "Tele1", "TR-HABER", ["tele 1"]),
    ("tgrthaber", "TGRT Haber", "TR-HABER", ["tgrt"]),
    ("haberglobal", "Haber Global", "TR-HABER", []),
    ("tv100", "tv100", "TR-HABER", ["tv 100"]),
    ("bloomberght", "Bloomberg HT", "TR-HABER", ["bloomberg"]),
    ("cnbce", "CNBC-e", "TR-HABER", ["cnbc e"]),
    ("ekoturk", "Ekotürk", "TR-HABER", ["ekoturk tv"]),
    ("ekoltv", "Ekol TV", "TR-HABER", []),
    ("apara", "A Para", "TR-HABER", []),
    ("bikanal", "Bi Kanal", "TR-HABER", []),
    ("yenicagtv", "Yeniçağ TV", "TR-HABER", []),
    ("flashhaber", "Flash Haber", "TR-HABER", ["flash haber tv"]),
    ("tv5", "TV5", "TR-HABER", []),
    ("akittv", "Akit TV", "TR-HABER", []),
    ("liderhaber", "Lider Haber", "TR-HABER", []),
    ("finansturk", "Finanstürk", "TR-HABER", ["finansturk tv"]),
    ("olayturk", "Olay Türk", "TR-HABER", ["olayturk tv"]),
    ("turkhaber", "Türk Haber", "TR-HABER", ["turk haber tv"]),
    # ---------------------------------------------------------------- spor
    ("trtspor", "TRT Spor", "TR-SPOR", []),
    ("trtsporyildiz", "TRT Spor Yıldız", "TR-SPOR", ["trt spor 2", "trt spor yildiz"]),
    ("aspor", "A Spor", "TR-SPOR", []),
    ("beinsportshaber", "beIN Sports Haber", "TR-SPOR", ["bein haber"]),
    ("htspor", "HT Spor", "TR-SPOR", []),
    ("fbtv", "FB TV", "TR-SPOR", []),
    ("gstv", "GS TV", "TR-SPOR", []),
    ("bjktv", "BJK TV", "TR-SPOR", []),
    ("ekolsports", "Ekol Sports", "TR-SPOR", ["ekol sport tv", "ekolsport"]),
    ("sportstv", "Sports TV", "TR-SPOR", []),
    # ---------------------------------------------------------------- çocuk
    ("trtcocuk", "TRT Çocuk", "TR-ÇOCUK", ["trt cocuk"]),
    ("trtdiyanetcocuk", "TRT Diyanet Çocuk", "TR-ÇOCUK", ["trt diyanet cocuk"]),
    ("minikacocuk", "Minika Çocuk", "TR-ÇOCUK", ["minika cocuk"]),
    ("minikago", "Minika Go", "TR-ÇOCUK", []),
    ("cartoonnetwork", "Cartoon Network", "TR-ÇOCUK", []),
    ("spacetoon", "Spacetoon", "TR-ÇOCUK", ["spacetoon turkey"]),
    ("trtgenc", "TRT Genç", "TR-ÇOCUK", ["trt genc tv"]),
    ("trteba", "TRT EBA", "TR-ÇOCUK", []),
    # ---------------------------------------------------------------- belgesel
    ("trtbelgesel", "TRT Belgesel", "TR-BELGESEL", []),
    # ---------------------------------------------------------------- müzik
    ("trtmuzik", "TRT Müzik", "TR-MÜZİK", ["trt muzik"]),
    ("kralpop", "Kral Pop", "TR-MÜZİK", ["kral pop tv"]),
    ("powerturk", "PowerTürk TV", "TR-MÜZİK", ["powerturk tv", "power turk"]),
    ("powertv", "Power TV", "TR-MÜZİK", []),
    ("numberone", "Number1", "TR-MÜZİK", ["number1 tv", "number one", "nr1"]),
    ("numberoneturk", "Number1 Türk", "TR-MÜZİK", ["number1 turk", "numberone turk"]),
    ("dreamturk", "Dream Türk", "TR-MÜZİK", []),
]

# Katalog dışı adlarda Türkiye'yle ilgili olduğunu gösteren işaretler.
_TR_TOKENS = {"turk", "turkiye", "haber", "kanal", "trt", "spor", "yerel", "kent",
              "belediye", "medya", "televizyon", "muzik", "cocuk", "belgesel", "karadeniz",
              "anadolu", "ege", "akdeniz", "guneydogu", "dogu", "postasi", "postasi"}
_TR_CHARS = set("çğışöüÇĞİŞÖÜ")
_FOREIGN_RE = re.compile(
    r"\b(news channel|fox news|fox sports|deportes|espanol|español|usa|telugu|tamil|hindi|"
    r"pluto|drew barrymore|daily show|graham norton|game ?show|star (maa|vijay|pravah|utsav|jalsha)|"
    r"turkmenistan|madinah|makkah|thaqalayn|fashion ?one|lone star)\b", re.I)


def key_of(name):
    """İsimden karşılaştırma anahtarı: 'TR: TRT-1 FHD' → 'trt1'."""
    k = fold(clean_name(name or ""))
    return re.sub(r"[^a-z0-9]+", "", k)


class Registry:
    def __init__(self):
        self.by_key = {}       # anahtar → kimlik
        self.meta = {}         # kimlik → {name, group, order, tvg_id, logo}
        for i, (cid, nm, grp, aliases) in enumerate(CATALOG):
            self.meta[cid] = {"name": nm, "group": grp, "order": i, "tvg_id": "", "logo": ""}
            for a in [cid, nm, *aliases]:
                self._add(key_of(a), cid)
        self.enriched = 0

    def _add(self, key, cid):
        if not key:
            return
        self.by_key.setdefault(key, cid)
        # "halk" ↔ "halktv" eşleşsin
        if key.endswith("tv") and len(key) > 4:
            self.by_key.setdefault(key[:-2], cid)
        elif len(key) >= 3 and not key[-1].isdigit():
            self.by_key.setdefault(key + "tv", cid)

    # ------------------------------------------------------------- iptv-org
    def enrich(self, channels_json, logos_json=None):
        """iptv-org veritabanından TR kanallarının alternatif adları, tvg-id ve logoları."""
        if not channels_json:
            return
        logos = {}
        for lg in logos_json or []:
            cid = lg.get("channel")
            if cid and lg.get("url") and cid not in logos:
                logos[cid] = lg["url"]
        for ch in channels_json:
            if (ch.get("country") or "").upper() != "TR" or ch.get("closed"):
                continue
            names = [ch.get("name", "")] + list(ch.get("alt_names") or [])
            keys = [key_of(n) for n in names if n]
            ours = next((self.by_key[k] for k in keys if k in self.by_key), None)
            if not ours:
                continue
            m = self.meta[ours]
            if not m["tvg_id"]:
                m["tvg_id"] = ch.get("id", "")
            if not m["logo"]:
                m["logo"] = ch.get("logo") or logos.get(ch.get("id"), "")
            for k in keys:
                self._add(k, ours)
            self.enriched += 1
        log.info("iptv-org ile zenginleştirilen kanal: %d", self.enriched)

    # ------------------------------------------------------------- ana işlev
    def resolve(self, ch):
        """Kanala kimlik ver. Döndürür: (cid, bilinen_mi)."""
        for cand in (ch.raw_name, ch.name, ch.tvg_id.split(".")[0] if ch.tvg_id else ""):
            k = key_of(cand)
            if k in self.by_key:
                return self.by_key[k], True
        k = key_of(ch.name)
        return ("x-" + k) if k else "", False

    def is_known(self, cid):
        return cid in self.meta

    def tr_relevant(self, ch, known, source_is_tr=False):
        """Katalog dışı kanal Türkiye'yle ilgili mi? (yabancı çöpü ayıklar)"""
        if known or ch.armored:
            return True
        nm = ch.raw_name or ch.name
        if _FOREIGN_RE.search(nm):
            return False
        if source_is_tr:
            return True
        if any(c in _TR_CHARS for c in nm):
            return True
        # Not: ch.group burada kullanılmaz — eski listelerde yabancı kanallar da "TR-ULUSAL" olabiliyor.
        toks = set(re.split(r"[^a-z0-9]+", fold(nm)))
        if toks & _TR_TOKENS:
            return True
        src = fold(ch.source)
        return any(t in src for t in ("turk", "/tr.m3u", "/tr/", "_tr.", "-tr.", "turkey", "trt"))


def load_registry(fetch_json=None):
    reg = Registry()
    if C.ENRICH_ENABLED and fetch_json:
        try:
            reg.enrich(fetch_json(C.IPTV_ORG_CHANNELS), fetch_json(C.IPTV_ORG_LOGOS))
        except Exception as e:  # zenginleştirme isteğe bağlıdır
            log.warning("iptv-org zenginleştirme atlandı: %s", e)
    return reg
