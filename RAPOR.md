# PuuStream IPTV Motoru — Güncelleme Raporu

**Tarih:** 19-11-2026 10:27 (TSİ) · **Test bölgesi:** github · **Süre:** 8 dk 0 sn

✅ **Yayınlandı.** Koruma: kontroller geçti

## Özet

| | |
|---|---|
| Sağlam kanal (en az 1 çalışan kaynak) | **493** |
| Yedek kaynağı olan kanal (≥2 sağlam) | 202 |
| tr.m3u otomatik bölüm kaydı | 695 |
| Test edilen adres | 1638 (derin/FFprobe: 500) |
| Sonuç | ✅ 1212 sağlam · ⚠️ 42 kararsız · 🚫 55 engelli · ❌ 329 ölü |
| Karantinada (bu tur atlandı) | 486 |
| Kaynak listesi | 155/164 indirildi |
| Site çözücüleri (7 spor kaynağı) | 94 aday (sağlık testine tabi) |
| Aday (hafızadan geri çağrılan) | 2123 (610) |
| Resmî site çözücüleri · JSON veritabanı · kardeş sunucu | 11 · 151 · 142 aday |
| Türk listesi sayılan kaynak | 168 |
| Yabancı olduğu için indirilmeyen dosya | 2453 |
| Elenen | credential: 4094, paid: 565, banned: 1351, foreign: 2646 |

## Zırhlı kanallar

- Kimlik: **1** kanal (1 kayıt)
- Sağlam: **0** · Çalışmayan: **1**
- Kendi adresi bozuk ama otomatik yedekle kurtarılan: **0**
- ⚠️ Zırhlı listede kullanıcı adı/şifre içeren **1** adres var. Depo herkese açıksa bu hesap bilgileri herkes tarafından görülebilir.

<details><summary>Çalışmayan zırhlı kanallar</summary>

- GET PHP USERNAME IOS&PASSWORD SINETECH&TYPE M3U_PLUS — 1 kayıt · segment not media

</details>

## Gruplara göre sağlam kanallar

- **TR-DİĞER:** 153
- **TR-YEREL:** 124
- **TR-ULUSAL:** 53
- **TR-HABER:** 48
- **TR-MÜZİK:** 38
- **TR-DİNİ:** 22
- **TR-BELGESEL:** 18
- **TR-SPOR:** 17
- **TR-ÇOCUK:** 17
- **TR-SİNEMA:** 3

## En iyi 20 kanal (puan)

| Kanal | Puan | Sağlam kaynak | Çözünürlük | Açılış |
|---|---|---|---|---|
| Kanal D | 100 | 6 | 1080p | 759 ms |
| Show TV | 100 | 6 | 1080p | 565 ms |
| Star TV | 100 | 6 | 1080p | 501 ms |
| NOW | 100 | 6 | 1080p | 307 ms |
| TV8 | 100 | 6 | 1080p | 192 ms |
| Beyaz TV | 100 | 6 | 1080p | 498 ms |
| 360 | 100 | 6 | 1080p | 496 ms |
| Teve2 | 100 | 6 | 1080p | 96 ms |
| TV8,5 | 100 | 6 | 1080p | 815 ms |
| TV4 | 100 | 6 | 1080p | 606 ms |
| A2 | 100 | 6 | 1080p | 277 ms |
| TRT Türk | 100 | 6 | 1080p | 917 ms |
| TRT Avaz | 100 | 6 | 1080p | 593 ms |
| TRT Kurdî | 100 | 6 | 1080p | 474 ms |
| TRT Arabi | 100 | 5 | 1080p | 922 ms |
| Show Max | 100 | 6 | 1080p | 839 ms |
| Show Türk | 100 | 1 | 1080p | 170 ms |
| Kanal 7 Avrupa | 100 | 6 | 1080p | 421 ms |
| TV 24 | 100 | 6 | 1080p | 255 ms |
| TYT Türk | 100 | 2 | 1080p | 560 ms |

## En verimli kaynaklar

- 239 sağlam · `https://raw.githubusercontent.com/YosemiteSam6/turkiye-iptv-m3u-m3u8/main/kanallar.m3u`
- 137 sağlam · `https://raw.githubusercontent.com/omerdenizhan/IPTV-M3U/main/m3u/turkiye-iptv-org.m3u`
- 105 sağlam · `https://raw.githubusercontent.com/raalbatros/iptv/HEAD/176.m3u`
- 60 sağlam · `https://raw.githubusercontent.com/hussobaba/tbrt_medya/HEAD/Huseyin_cvk_tv.m3u8`
- 45 sağlam · `https://onureroz.com/indirmeler/turk/index.m3u`
- 44 sağlam · `https://raw.githubusercontent.com/MediaVizo/Premium1/HEAD/Giri%C5%9F%20Paketi.m3u8`
- 36 sağlam · `https://raw.githubusercontent.com/Yusufdkci/iptv/main/liste.m3u`
- 33 sağlam · `https://raw.githubusercontent.com/kodlama155-ctrl/tv/main/tr.m3u`
- 33 sağlam · `https://raw.githubusercontent.com/kodlama155-ctrl/tv/main/discovered.m3u`
- 33 sağlam · `https://raw.githubusercontent.com/braveheart1983/ataktv/HEAD/ataktv.m3u`
- 29 sağlam · `https://raw.githubusercontent.com/BoranT-3000/PlayerM3U8/HEAD/data/master_all_channels.m3u8`
- 25 sağlam · `https://raw.githubusercontent.com/bugsfreeweb/LiveTVCollector/HEAD/BugsfreeStreams/Output/StreamLinks-TR.m3u`
- 24 sağlam · `https://raw.githubusercontent.com/ridvanseref37/tivi-rs-playlist/main/Tivi_RS_M3U_Listesi.m3u`
- 20 sağlam · `https://raw.githubusercontent.com/iptv-turk-tr/iptv/main/list.m3u`
- 20 sağlam · `https://raw.githubusercontent.com/famelack/famelack-data/main/tv/countries/tr.json`

## Ölü/engelli nedenleri

- connect: 101
- timeout: 84
- http 404: 76
- http 403: 41
- segment http 403: 12
- http 421: 11
- variant http 404: 9
- variant http 500: 9
- vod: 7
- http 500: 5
- http 503: 4
- not media: 4

_iptv-org ile zenginleştirilen kanal: 97_
