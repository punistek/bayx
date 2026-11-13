# PuuStream IPTV Motoru — Güncelleme Raporu

**Tarih:** 13-11-2026 22:47 (TSİ) · **Test bölgesi:** github · **Süre:** 9 dk 4 sn

✅ **Yayınlandı.** Koruma: kontroller geçti

## Özet

| | |
|---|---|
| Sağlam kanal (en az 1 çalışan kaynak) | **492** |
| Yedek kaynağı olan kanal (≥2 sağlam) | 193 |
| tr.m3u otomatik bölüm kaydı | 685 |
| Test edilen adres | 1534 (derin/FFprobe: 500) |
| Sonuç | ✅ 1180 sağlam · ⚠️ 34 kararsız · 🚫 264 engelli · ❌ 56 ölü |
| Karantinada (bu tur atlandı) | 554 |
| Kaynak listesi | 143/152 indirildi |
| Site çözücüleri (7 spor kaynağı) | 94 aday (sağlık testine tabi) |
| Aday (hafızadan geri çağrılan) | 2088 (584) |
| Resmî site çözücüleri · JSON veritabanı · kardeş sunucu | 10 · 149 · 141 aday |
| Türk listesi sayılan kaynak | 160 |
| Yabancı olduğu için indirilmeyen dosya | 2451 |
| Elenen | paid: 521, banned: 1326, credential: 25, foreign: 3503 |

## Zırhlı kanallar

- Kimlik: **0** kanal (0 kayıt)
- Sağlam: **0** · Çalışmayan: **0**
- Kendi adresi bozuk ama otomatik yedekle kurtarılan: **0**

## Gruplara göre sağlam kanallar

- **TR-DİĞER:** 148
- **TR-YEREL:** 134
- **TR-ULUSAL:** 51
- **TR-HABER:** 45
- **TR-MÜZİK:** 36
- **TR-DİNİ:** 22
- **TR-ÇOCUK:** 19
- **TR-SPOR:** 17
- **TR-BELGESEL:** 17
- **TR-SİNEMA:** 3

## En iyi 20 kanal (puan)

| Kanal | Puan | Sağlam kaynak | Çözünürlük | Açılış |
|---|---|---|---|---|
| Kanal D | 100 | 6 | 1080p | 450 ms |
| Show TV | 100 | 6 | 1080p | 248 ms |
| TV8 | 100 | 6 | 1080p | 311 ms |
| Beyaz TV | 100 | 6 | 1080p | 817 ms |
| 360 | 100 | 6 | 1080p | 918 ms |
| Teve2 | 100 | 6 | 1080p | 933 ms |
| TV8,5 | 100 | 6 | 1080p | 434 ms |
| TV4 | 100 | 6 | 1080p | 152 ms |
| A2 | 100 | 6 | 1080p | 339 ms |
| TRT Türk | 100 | 6 | 1080p | 659 ms |
| TRT Avaz | 100 | 6 | 1080p | 616 ms |
| TRT Kurdî | 100 | 6 | 1080p | 889 ms |
| TRT Arabi | 100 | 5 | 1080p | 238 ms |
| Show Max | 100 | 6 | 1080p | 875 ms |
| Kanal 7 Avrupa | 100 | 6 | 1080p | 646 ms |
| tabii TV | 100 | 3 | 1080p | 791 ms |
| TV 24 | 100 | 6 | 1080p | 225 ms |
| TYT Türk | 100 | 2 | 1080p | 862 ms |
| Vav TV | 100 | 3 | 1080p | 614 ms |
| Ton TV | 100 | 2 | 1080p | 405 ms |

## En verimli kaynaklar

- 233 sağlam · `https://raw.githubusercontent.com/YosemiteSam6/turkiye-iptv-m3u-m3u8/main/kanallar.m3u`
- 135 sağlam · `https://raw.githubusercontent.com/omerdenizhan/IPTV-M3U/main/m3u/turkiye-iptv-org.m3u`
- 109 sağlam · `https://raw.githubusercontent.com/raalbatros/iptv/HEAD/176.m3u`
- 83 sağlam · `https://raw.githubusercontent.com/hussobaba/tbrt_medya/HEAD/Huseyin_cvk_tv.m3u8`
- 45 sağlam · `https://onureroz.com/indirmeler/turk/index.m3u`
- 43 sağlam · `https://raw.githubusercontent.com/MediaVizo/Premium1/HEAD/Giri%C5%9F%20Paketi.m3u8`
- 40 sağlam · `https://raw.githubusercontent.com/Yusufdkci/iptv/main/liste.m3u`
- 30 sağlam · `https://raw.githubusercontent.com/kodlama155-ctrl/tv/main/tr.m3u`
- 29 sağlam · `https://raw.githubusercontent.com/kodlama155-ctrl/tv/main/discovered.m3u`
- 25 sağlam · `https://raw.githubusercontent.com/bugsfreeweb/LiveTVCollector/HEAD/BugsfreeStreams/Output/StreamLinks-TR.m3u`
- 24 sağlam · `https://raw.githubusercontent.com/ridvanseref37/tivi-rs-playlist/main/Tivi_RS_M3U_Listesi.m3u`
- 19 sağlam · `https://raw.githubusercontent.com/famelack/famelack-data/main/tv/countries/tr.json`
- 18 sağlam · `https://raw.githubusercontent.com/iptv-turk-tr/iptv/main/list.m3u`
- 18 sağlam · `https://raw.githubusercontent.com/drsof1968/iptv/HEAD/francaises.m3u8`
- 17 sağlam · `https://raw.githubusercontent.com/levi-45/iptvstream/HEAD/TURK_ULUSAL_IPTV.m3u`

## Ölü/engelli nedenleri

- http 403: 209
- segment http 401: 34
- http 503: 17
- http 401: 12
- http 404: 12
- ffprobe: 9
- segment http 403: 6
- timeout: 4
- variant http 403: 3
- http 502: 3
- variant http 500: 2
- variant: 2

_iptv-org ile zenginleştirilen kanal: 97_
