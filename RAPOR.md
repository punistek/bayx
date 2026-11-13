# PuuStream IPTV Motoru — Güncelleme Raporu

**Tarih:** 13-11-2026 09:44 (TSİ) · **Test bölgesi:** github · **Süre:** 7 dk 31 sn

✅ **Yayınlandı.** Koruma: kontroller geçti

## Özet

| | |
|---|---|
| Sağlam kanal (en az 1 çalışan kaynak) | **491** |
| Yedek kaynağı olan kanal (≥2 sağlam) | 192 |
| tr.m3u otomatik bölüm kaydı | 683 |
| Test edilen adres | 1602 (derin/FFprobe: 500) |
| Sonuç | ✅ 1192 sağlam · ⚠️ 25 kararsız · 🚫 187 engelli · ❌ 198 ölü |
| Karantinada (bu tur atlandı) | 483 |
| Kaynak listesi | 143/152 indirildi |
| Site çözücüleri (7 spor kaynağı) | 94 aday (sağlık testine tabi) |
| Aday (hafızadan geri çağrılan) | 2085 (581) |
| Resmî site çözücüleri · JSON veritabanı · kardeş sunucu | 10 · 149 · 141 aday |
| Türk listesi sayılan kaynak | 157 |
| Yabancı olduğu için indirilmeyen dosya | 2451 |
| Elenen | paid: 521, banned: 1330, credential: 39, foreign: 3643 |

## Zırhlı kanallar

- Kimlik: **0** kanal (0 kayıt)
- Sağlam: **0** · Çalışmayan: **0**
- Kendi adresi bozuk ama otomatik yedekle kurtarılan: **0**

## Gruplara göre sağlam kanallar

- **TR-DİĞER:** 143
- **TR-YEREL:** 136
- **TR-ULUSAL:** 52
- **TR-HABER:** 47
- **TR-MÜZİK:** 38
- **TR-ÇOCUK:** 20
- **TR-SPOR:** 18
- **TR-BELGESEL:** 18
- **TR-DİNİ:** 16
- **TR-SİNEMA:** 3

## En iyi 20 kanal (puan)

| Kanal | Puan | Sağlam kaynak | Çözünürlük | Açılış |
|---|---|---|---|---|
| Kanal D | 100 | 6 | 1080p | 607 ms |
| Show TV | 100 | 6 | 1080p | 265 ms |
| TV8 | 100 | 6 | 1080p | 253 ms |
| Beyaz TV | 100 | 6 | 1080p | 490 ms |
| 360 | 100 | 6 | 1080p | 479 ms |
| Teve2 | 100 | 6 | 1080p | 802 ms |
| TV8,5 | 100 | 6 | 1080p | 373 ms |
| TV4 | 100 | 6 | 1080p | 217 ms |
| A2 | 100 | 6 | 1080p | 786 ms |
| TRT Türk | 100 | 6 | 1080p | 675 ms |
| TRT Avaz | 100 | 6 | 1080p | 641 ms |
| TRT Kurdî | 100 | 6 | 1080p | 897 ms |
| TRT Arabi | 100 | 5 | 1080p | 571 ms |
| Show Max | 100 | 6 | 1080p | 799 ms |
| Kanal 7 Avrupa | 100 | 6 | 1080p | 461 ms |
| tabii TV | 100 | 3 | 1080p | 516 ms |
| TV 24 | 100 | 6 | 1080p | 100 ms |
| TYT Türk | 100 | 2 | 1080p | 482 ms |
| Vav TV | 100 | 3 | 1080p | 377 ms |
| Ton TV | 100 | 2 | 1080p | 277 ms |

## En verimli kaynaklar

- 233 sağlam · `https://raw.githubusercontent.com/YosemiteSam6/turkiye-iptv-m3u-m3u8/main/kanallar.m3u`
- 135 sağlam · `https://raw.githubusercontent.com/omerdenizhan/IPTV-M3U/main/m3u/turkiye-iptv-org.m3u`
- 109 sağlam · `https://raw.githubusercontent.com/raalbatros/iptv/HEAD/176.m3u`
- 90 sağlam · `https://raw.githubusercontent.com/hussobaba/tbrt_medya/HEAD/Huseyin_cvk_tv.m3u8`
- 55 sağlam · `https://raw.githubusercontent.com/BoranT-3000/PlayerM3U8/HEAD/data/master_all_channels.m3u8`
- 47 sağlam · `https://onureroz.com/indirmeler/turk/index.m3u`
- 42 sağlam · `https://raw.githubusercontent.com/MediaVizo/Premium1/HEAD/Giri%C5%9F%20Paketi.m3u8`
- 36 sağlam · `https://raw.githubusercontent.com/Yusufdkci/iptv/main/liste.m3u`
- 30 sağlam · `https://raw.githubusercontent.com/kodlama155-ctrl/tv/main/discovered.m3u`
- 28 sağlam · `https://raw.githubusercontent.com/kodlama155-ctrl/tv/main/tr.m3u`
- 26 sağlam · `https://raw.githubusercontent.com/bugsfreeweb/LiveTVCollector/HEAD/BugsfreeStreams/Output/StreamLinks-TR.m3u`
- 24 sağlam · `https://raw.githubusercontent.com/ridvanseref37/tivi-rs-playlist/main/Tivi_RS_M3U_Listesi.m3u`
- 19 sağlam · `https://raw.githubusercontent.com/iptv-turk-tr/iptv/main/list.m3u`
- 19 sağlam · `https://raw.githubusercontent.com/famelack/famelack-data/main/tv/countries/tr.json`
- 16 sağlam · `https://raw.githubusercontent.com/allthethingsyouhavechased-ui/tv-liste/main/k.m3u`

## Ölü/engelli nedenleri

- http 403: 139
- connect: 110
- http 404: 33
- segment http 401: 23
- timeout: 22
- segment http 403: 16
- http 503: 12
- http 401: 9
- ffprobe: 8
- vod: 4
- http 421: 3
- variant http 500: 2

_iptv-org ile zenginleştirilen kanal: 97_
