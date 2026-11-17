# PuuStream IPTV Motoru — Güncelleme Raporu

**Tarih:** 18-11-2026 00:03 (TSİ) · **Test bölgesi:** github · **Süre:** 11 dk 20 sn

✅ **Yayınlandı.** Koruma: kontroller geçti

## Özet

| | |
|---|---|
| Sağlam kanal (en az 1 çalışan kaynak) | **523** |
| Yedek kaynağı olan kanal (≥2 sağlam) | 197 |
| tr.m3u otomatik bölüm kaydı | 720 |
| Test edilen adres | 3146 (derin/FFprobe: 500) |
| Sonuç | ✅ 1134 sağlam · ⚠️ 146 kararsız · 🚫 698 engelli · ❌ 1168 ölü |
| Karantinada (bu tur atlandı) | 1261 |
| Kaynak listesi | 322/335 indirildi |
| Site çözücüleri (7 spor kaynağı) | 94 aday (sağlık testine tabi) |
| Aday (hafızadan geri çağrılan) | 4406 (320) |
| Resmî site çözücüleri · JSON veritabanı · kardeş sunucu | 11 · 153 · 142 aday |
| Türk listesi sayılan kaynak | 205 |
| Yabancı olduğu için indirilmeyen dosya | 2453 |
| Elenen | paid: 1636, banned: 4339, credential: 9683, foreign: 20954 |

## Zırhlı kanallar

- Kimlik: **1** kanal (1 kayıt)
- Sağlam: **0** · Çalışmayan: **1**
- Kendi adresi bozuk ama otomatik yedekle kurtarılan: **0**
- ⚠️ Zırhlı listede kullanıcı adı/şifre içeren **1** adres var. Depo herkese açıksa bu hesap bilgileri herkes tarafından görülebilir.

<details><summary>Çalışmayan zırhlı kanallar</summary>

- GET PHP USERNAME IOS&PASSWORD SINETECH&TYPE M3U_PLUS — 1 kayıt · segment not media

</details>

## Gruplara göre sağlam kanallar

- **TR-DİĞER:** 148
- **TR-YEREL:** 136
- **TR-HABER:** 58
- **TR-ULUSAL:** 57
- **TR-MÜZİK:** 43
- **TR-DİNİ:** 23
- **TR-SPOR:** 19
- **TR-ÇOCUK:** 18
- **TR-BELGESEL:** 18
- **TR-SİNEMA:** 3

## En iyi 20 kanal (puan)

| Kanal | Puan | Sağlam kaynak | Çözünürlük | Açılış |
|---|---|---|---|---|
| TRT 1 | 100 | 6 | 1080p | 740 ms |
| Kanal D | 100 | 6 | 1080p | 632 ms |
| Show TV | 100 | 6 | 1080p | 252 ms |
| Star TV | 100 | 6 | 1080p | 616 ms |
| TV8 | 100 | 6 | 1080p | 322 ms |
| Beyaz TV | 100 | 6 | 1080p | 802 ms |
| 360 | 100 | 6 | 1080p | 927 ms |
| Teve2 | 100 | 6 | 1080p | 160 ms |
| TV4 | 100 | 6 | 1080p | 142 ms |
| A2 | 100 | 6 | 1080p | 160 ms |
| TRT Türk | 100 | 6 | 1080p | 801 ms |
| TRT Avaz | 100 | 6 | 1080p | 509 ms |
| TRT Kurdî | 100 | 6 | 1080p | 355 ms |
| TRT Arabi | 100 | 5 | 1080p | 238 ms |
| Show Max | 100 | 6 | 1080p | 792 ms |
| Show Türk | 100 | 1 | 1080p | 655 ms |
| Kanal 7 Avrupa | 100 | 6 | 1080p | 645 ms |
| TV 24 | 100 | 6 | 1080p | 296 ms |
| TYT Türk | 100 | 2 | 1080p | 864 ms |
| Vav TV | 100 | 3 | 1080p | 627 ms |

## En verimli kaynaklar

- 235 sağlam · `https://raw.githubusercontent.com/YosemiteSam6/turkiye-iptv-m3u-m3u8/main/kanallar.m3u`
- 137 sağlam · `https://raw.githubusercontent.com/omerdenizhan/IPTV-M3U/main/m3u/turkiye-iptv-org.m3u`
- 111 sağlam · `https://raw.githubusercontent.com/raalbatros/iptv/HEAD/176.m3u`
- 61 sağlam · `https://raw.githubusercontent.com/hussobaba/tbrt_medya/HEAD/Huseyin_cvk_tv.m3u8`
- 45 sağlam · `https://raw.githubusercontent.com/MediaVizo/Premium1/HEAD/Giri%C5%9F%20Paketi.m3u8`
- 43 sağlam · `https://onureroz.com/indirmeler/turk/index.m3u`
- 43 sağlam · `https://raw.githubusercontent.com/Yusufdkci/iptv/main/liste.m3u`
- 35 sağlam · `https://raw.githubusercontent.com/braveheart1983/ataktv/HEAD/ataktv.m3u`
- 33 sağlam · `https://raw.githubusercontent.com/kodlama155-ctrl/tv/main/discovered.m3u`
- 32 sağlam · `https://raw.githubusercontent.com/kodlama155-ctrl/tv/main/tr.m3u`
- 31 sağlam · `https://raw.githubusercontent.com/BoranT-3000/PlayerM3U8/HEAD/data/master_all_channels.m3u8`
- 25 sağlam · `https://raw.githubusercontent.com/bugsfreeweb/LiveTVCollector/HEAD/BugsfreeStreams/Output/StreamLinks-TR.m3u`
- 24 sağlam · `https://raw.githubusercontent.com/ridvanseref37/tivi-rs-playlist/main/Tivi_RS_M3U_Listesi.m3u`
- 18 sağlam · `https://raw.githubusercontent.com/iptv-turk-tr/iptv/main/list.m3u`
- 18 sağlam · `https://raw.githubusercontent.com/famelack/famelack-data/main/tv/countries/tr.json`

## Ölü/engelli nedenleri

- connect: 604
- http 403: 585
- http 404: 237
- timeout: 228
- http 401: 83
- not media: 15
- segment http 403: 14
- http 421: 13
- segment http 401: 12
- http 500: 10
- segment http 404: 8
- http 302: 8

_iptv-org ile zenginleştirilen kanal: 97_
