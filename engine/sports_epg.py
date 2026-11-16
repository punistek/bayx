# -*- coding: utf-8 -*-
"""
Yayın akışından (XMLTV) CANLI MAÇLARI bulur → maclar.json

Uygulama (PuuStream TV) bu küçük dosyayı okur ve radyo skalasında "⚽ CANLI MAÇ" istasyonu
gösterir. Akışın tamamı telefona İNMEZ (eski TV kutularını yormasın diye): ağır iş burada.

Ne yapar:
  1. EPG_URLS'teki XMLTV dosyalarını (.xml / .xml.gz) akış halinde okur (bellek dostu iterparse).
  2. Şimdi-3 saat … şimdi+30 saat arasındaki programlara bakar.
  3. Maç olanları seçer:
       - "Galatasaray - Fenerbahçe", "Man City vs Arsenal", "Efes – Real Madrid" (takım – takım)
       - ya da başlıkta "Canlı / (C) / Live / Naklen" + spor türü
       - Tekrar, özet, stüdyo, maç önü/sonu, analiz ELENİR.
       - Spor kanalı olmayan kanallarda (TRT 1, ATV, TV8…) "takım – takım" yetmez: spor türü
         ya da "canlı" işareti de gerekir (dizi bölümleri "Dizi - 170. Bölüm" karışmasın).
  4. Kanal adını OLDUĞU GİBİ yazar. Uygulama onu kendi listesinde (bot + CloudStream eklentileri)
     kendi kuralıyla eşler: beIN Sports gibi eklentiden gelen kanallar da bulunur.

Çıktı (maclar.json):
  {"version":1, "generated_at":<sn>, "matches":[
     {"kanal":"beIN SPORTS 1","tvg":"beINSports1.tr","baslik":"Galatasaray - Fenerbahçe",
      "lig":"Trendyol Süper Lig","tur":"futbol","bas":<sn>,"bit":<sn>,"canli":true}, …]}
"""
import gzip
import io
import json
import logging
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

log = logging.getLogger("sports_epg")

GERI_SAAT = 3          # bitmemiş uzun maçlar da gelsin
ILERI_SAAT = 30        # bot 2-3 saatte bir çalışsa da yarına kadar kapsar
MAX_BYTES = 200 * 1024 * 1024  # açılmış XML üst sınırı (bozuk/dev dosyaya karşı)


def _fold(s):
    s = (s or "").lower()
    for a, b in (("ı", "i"), ("İ", "i"), ("i̇", "i"), ("ş", "s"), ("ğ", "g"), ("ü", "u"),
                 ("ö", "o"), ("ç", "c"), ("â", "a"), ("î", "i"), ("û", "u")):
        s = s.replace(a, b)
    return s


# Elenen programlar (tekrar / özet / stüdyo …)
_HARIC = re.compile(
    r"\b(tekrar|ozet|ozetler|highlights?|replay|magazin|studyo|studio|analiz|degerlendirme|yorum|"
    r"mac\s*sonu|mac\s*onu|macin\s*ardindan|oncesi|sonrasi|gol\s*sov|golleri|belgesel|dizi|film|"
    r"bolum|sezon\s*\d|episode|haber|bulten|program|tanitim|fragman|klasik|nostalji|"
    r"preview|review|magazine|classic)\b|\((t|r|tekrar)\)")
# Canlı işareti
# İngilizce "live" yalnız başta/sonda ya da parantezde ("Only Live Once" gibi adlar sayılmasın).
_CANLI = re.compile(r"\b(canli|naklen|en\s*direct|en\s*vivo)\b|^\s*live\b|\blive\s*$|"
                    r"\(c\)|\(canli\)|\(live\)")
# Takım – takım ("A - B", "A vs B", "A v B", "A – B")
_VS = re.compile(r"^\s*(.{2,40}?)\s+(?:-|–|—|vs\.?|v\.?|x)\s+(.{2,40}?)\s*(?:\(.*\))?\s*$", re.I)
# Spor türleri (kategori ya da başlık/açıklamada)
_TUR = [
    ("basketbol", r"basketbol|basketball|nba|euroleague|eurocup|bsl\b|basket"),
    ("voleybol", r"voleybol|volleyball|sultanlar|efeler"),
    ("tenis", r"tenis|tennis|atp\b|wta\b|wimbledon|roland|us open|australian open"),
    ("motor", r"formula|\bf1\b|motogp|moto gp|rally|ralli|nascar|indycar|wec\b"),
    ("dovus", r"\bboks\b|boxing|\bufc\b|\bmma\b|gures|wrestling|kickboks"),
    ("hentbol", r"hentbol|handball"),
    ("futbol", r"futbol|football|soccer|super lig|1\.\s*lig|premier lig|premier league|la liga|"
               r"serie a|bundesliga|ligue 1|sampiyonlar ligi|champions league|avrupa ligi|"
               r"europa league|konferans ligi|conference league|turkiye kupasi|ziraat|uefa|fifa|"
               r"dunya kupasi|world cup|euro 20|uluslar ligi|nations league|milli mac"),
]
_SPOR_KAT = re.compile(r"spor|sport|futbol|football|soccer|basket|voley|volley|tenis|tennis|"
                       r"formula|motor|boks|boxing|ufc|mma|hentbol|handball|atletizm|athletics")
# Spor kanalı mı? (adında)
_SPOR_KANAL = re.compile(r"spor|sport|bein|eurosport|nba|tivibu|exxen|smart\s*spor|s\s*sport|"
                         r"ssport|trt\s*3|tabii\s*spor|dazn|arena|espn|sky\s*sport|tjk|euroleague")


def _tur(text):
    t = _fold(text)
    for ad, rx in _TUR:
        if re.search(rx, t):
            return ad
    return ""


def parse_xmltv_time(s):
    """'20261115200000 +0300' → epoch saniye. Hatalıysa None."""
    s = (s or "").strip()
    m = re.match(r"^(\d{12})(\d{2})?\s*([+-]\d{4})?", s)
    if not m:
        return None
    dt = datetime.strptime(m.group(1) + (m.group(2) or "00"), "%Y%m%d%H%M%S")
    off = m.group(3)
    if off:
        sign = 1 if off[0] == "+" else -1
        tz = timezone(sign * timedelta(hours=int(off[1:3]), minutes=int(off[3:5])))
    else:
        tz = timezone.utc
    return int(dt.replace(tzinfo=tz).timestamp())


def mac_mi(baslik, kanal_adi, kategoriler=(), alt_baslik="", aciklama=""):
    """Bu program canlı yayınlanan bir maç mı? → (evet_mi, tür)"""
    t = _fold(baslik)
    if not t or _HARIC.search(t):
        return False, ""
    kat = _fold(" ".join(kategoriler))
    ek = _fold(alt_baslik + " " + aciklama[:300])
    spor_kat = bool(_SPOR_KAT.search(kat))
    spor_kanal = bool(_SPOR_KANAL.search(_fold(kanal_adi)))
    canli = bool(_CANLI.search(t) or _CANLI.search(_fold(alt_baslik)))
    if _HARIC.search(_fold(alt_baslik)):
        return False, ""
    temiz = re.sub(r"\((c|canli|live)\)|\b(canli|naklen|live)\b\s*[:\-]?", " ", t).strip(" :-")
    vs = _VS.match(temiz)
    if vs:
        a, b = vs.group(1).strip(), vs.group(2).strip()
        # "Dizi - 170. Bölüm", "Haberler - 19:00" gibi yanlış eşleşmeler
        if re.fullmatch(r"[\d\s.:]+", a) or re.fullmatch(r"[\d\s.:]+", b) or re.search(r"\d+\.\s*bolum", b):
            vs = None
    tur = _tur(kat) or _tur(t) or _tur(ek)
    if vs:
        if spor_kanal or spor_kat or canli or tur:
            return True, tur or "futbol"
        return False, ""
    # takım – takım yok: canlı + spor (ör. "Formula 1 Brezilya GP Canlı", "NBA Canlı")
    # Spor TÜRÜ şart: spor kanalı adı tek başına yetmez ("Only Live Once" / TRACE SPORT).
    if canli and tur:
        return True, tur
    return False, ""


def _lig(alt_baslik, aciklama):
    for s in (alt_baslik, (aciklama or "").split(".")[0]):
        s = re.sub(r"\s+", " ", (s or "")).strip()
        if 2 < len(s) <= 70 and not _CANLI.fullmatch(_fold(s)):
            return s
    return ""


def _temiz_baslik(b):
    b = re.sub(r"\s*\((c|canlı|canli|live)\)\s*", " ", b, flags=re.I)
    b = re.sub(r"^\s*(canlı|canli|naklen|live)\s*[:\-]\s*", "", b, flags=re.I)
    b = re.sub(r"\s+(canlı|canli|naklen|live)\s*$", "", b, flags=re.I)
    return re.sub(r"\s+", " ", b).strip(" -:")


TR_SAAT = 3 * 3600      # İstanbul = UTC+3 (yaz saati yok)
TEKRAR_TOLERANS = 20 * 60   # aynı maç 20 dk'dan daha geç tekrar yayınlanıyorsa: tekrar
ZINCIR_TOLERANS = 3 * 60    # önceki program bu kadar yakın bitiyorsa "art arda"
SABAH_SAATLERI = range(2, 12)  # 02:00-11:59 başlayan futbol: neredeyse hep tekrar


def _mac_anahtari(baslik):
    """'İspanya – İngiltere' ile 'İspanya - İngiltere (C)' aynı maç."""
    t = _fold(_temiz_baslik(baslik))
    return re.sub(r"[^a-z0-9]", "", t)


def _mac_benzeri(baslik):
    """Başlık bir maç gibi mi (tekrar/özet olsa bile değil)? Art arda yayın tespiti için."""
    t = _fold(baslik)
    if not t or _HARIC.search(t):
        return False
    temiz = re.sub(r"\((c|canli|live)\)|\b(canli|naklen|live)\b\s*[:\-]?", " ", t).strip(" :-")
    return bool(_VS.match(temiz))


def _tekrar_mi(m, ilk_yayin, kanal_programlari):
    """Spor kanalları gece-gündüz maç TEKRARI yayınlıyor ve akışta çoğu "(Tekrar)" yazmıyor.
    Canlı işareti olmayan maç şu durumlarda tekrar sayılır:
      1) aynı maç akışta daha önce yayınlanmış,
      2) aynı kanalda bir maç biter bitmez başlıyor (tekrar kuşağı; canlı maçtan önce
         "maç önü"/stüdyo olur),
      3) futbol ve sabah 02:00-11:59 arası başlıyor."""
    if m["_onceden"]:
        return True
    if m["canli"]:
        return False
    if ilk_yayin.get(m["_anahtar"], m["bas"]) < m["bas"] - TEKRAR_TOLERANS:
        return True
    for bas, bit, mac in kanal_programlari.get(m["tvg"], ()):
        if mac and bas < m["bas"] and abs(bit - m["bas"]) <= ZINCIR_TOLERANS:
            return True
    if m["tur"] == "futbol" and ((m["bas"] + TR_SAAT) % 86400) // 3600 in SABAH_SAATLERI:
        return True
    return False


def scan_xmltv(stream, now=None):
    """XMLTV akışını okur, (tekrarları ayıklanmış) maç listesi döner.
    stream: bytes okuyabilen dosya nesnesi."""
    now = now or int(time.time())
    alt, ust = now - GERI_SAAT * 3600, now + ILERI_SAAT * 3600
    kanallar = {}   # id → görünen ad
    adaylar = []
    ilk_yayin = {}           # maç anahtarı → akıştaki en erken başlangıç (bütün dosya)
    kanal_programlari = {}   # kanal id → [(bas, bit, maç_mı)] (pencere + 12 sa geri)
    for _, el in ET.iterparse(stream, events=("end",)):
        tag = el.tag
        if tag == "channel":
            dn = el.find("display-name")
            kanallar[el.get("id", "")] = (dn.text or "").strip() if dn is not None else el.get("id", "")
            el.clear()
        elif tag == "programme":
            try:
                bas = parse_xmltv_time(el.get("start"))
                bit = parse_xmltv_time(el.get("stop"))
                if not bas:
                    continue
                # Bozuk süreler: bitişi yok/başlangıçtan önce → 2 sa; 4 saatten uzun maç → 2 sa 15 dk
                if not bit or bit <= bas:
                    bit = bas + 7200
                tl = el.find("title")
                baslik = (tl.text or "").strip() if tl is not None else ""
                cid = el.get("channel", "")
                mac = _mac_benzeri(baslik)
                if mac:
                    k = _mac_anahtari(baslik)
                    if k and bas < ilk_yayin.get(k, bas + 1):
                        ilk_yayin[k] = bas
                if bit > alt - 12 * 3600 and bas < ust:
                    kanal_programlari.setdefault(cid, []).append((bas, bit, mac))
                if bit > alt and bas < ust:
                    kanal = kanallar.get(cid, cid)
                    st = el.find("sub-title")
                    alt_b = (st.text or "").strip() if st is not None else ""
                    ds = el.find("desc")
                    acik = (ds.text or "").strip() if ds is not None else ""
                    kats = [(c.text or "") for c in el.findall("category")]
                    ok, tur = mac_mi(baslik, kanal, kats, alt_b, acik)
                    if ok:
                        if bit - bas > 4 * 3600:
                            bit = bas + 8100
                        adaylar.append({
                            "kanal": kanal, "tvg": cid, "baslik": _temiz_baslik(baslik)[:90],
                            "lig": _lig(alt_b, acik), "tur": tur, "bas": bas, "bit": bit,
                            "canli": bool(_CANLI.search(_fold(baslik + " " + alt_b))),
                            "_anahtar": _mac_anahtari(baslik),
                            # XMLTV'nin kendi "daha önce yayınlandı" işareti
                            "_onceden": el.find("previously-shown") is not None,
                        })
            except Exception as e:  # tek bozuk program tüm akışı düşürmesin
                log.debug("program atlandı: %s", e)
            finally:
                el.clear()
    out = []
    elenen = 0
    for m in adaylar:
        if _tekrar_mi(m, ilk_yayin, kanal_programlari):
            elenen += 1
            continue
        out.append({k: v for k, v in m.items() if not k.startswith("_")})
    log.info("Tekrar olduğu için elenen: %d", elenen)
    return out


def _open(url, session):
    r = session.get(url, timeout=60, stream=True)
    r.raise_for_status()
    raw = io.BytesIO()
    for chunk in r.iter_content(1 << 16):
        raw.write(chunk)
        if raw.tell() > MAX_BYTES:
            raise ValueError("dosya çok büyük")
    raw.seek(0)
    head = raw.read(2)
    raw.seek(0)
    return gzip.GzipFile(fileobj=raw) if head == b"\x1f\x8b" else raw


def build(urls, session, now=None):
    """Bütün akışlardan maçlar; aynı kanal + aynı başlangıç bir kez. Hiç akış okunamazsa None."""
    tum, okunan = [], 0
    for u in urls:
        try:
            tum += scan_xmltv(_open(u, session), now=now)
            okunan += 1
            log.info("EPG okundu: %s", u)
        except Exception as e:
            log.warning("EPG okunamadı (%s): %s", u, e)
    if not okunan:
        return None
    gor, out = set(), []
    for m in sorted(tum, key=lambda x: (x["bas"], x["kanal"].lower())):
        k = (re.sub(r"[^a-z0-9]", "", _fold(m["kanal"])), m["bas"])
        if k in gor:
            continue
        gor.add(k)
        out.append(m)
    return out


def write(path, matches, now=None):
    data = {"version": 1, "generated_at": int(now or time.time()), "matches": matches}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    return data
