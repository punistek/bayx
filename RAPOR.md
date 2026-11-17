# PuuStream IPTV Motoru — Güncelleme Raporu

**Tarih:** 18-11-2026 00:15 (TSİ) · **Test bölgesi:** github · **Süre:** 7 dk 19 sn

✅ **Yayınlandı.** Koruma: kontroller geçti

## Özet

| | |
|---|---|
| Sağlam kanal (en az 1 çalışan kaynak) | **502** |
| Yedek kaynağı olan kanal (≥2 sağlam) | 199 |
| tr.m3u otomatik bölüm kaydı | 701 |
| Test edilen adres | 1304 (derin/FFprobe: 500) |
| Sonuç | ✅ 1219 sağlam · ⚠️ 36 kararsız · 🚫 33 engelli · ❌ 16 ölü |
| Karantinada (bu tur atlandı) | 818 |
| Kaynak listesi | 148/157 indirildi |
| Site çözücüleri (7 spor kaynağı) | 94 aday (sağlık testine tabi) |
| Aday (hafızadan geri çağrılan) | 2121 (604) |
| Resmî site çözücüleri · JSON veritabanı · kardeş sunucu | 11 · 153 · 142 aday |
| Türk listesi sayılan kaynak | 162 |
| Yabancı olduğu için indirilmeyen dosya | 2453 |
| Elenen | credential: 4117, paid: 531, banned: 1323, foreign: 2629 |

## Zırhlı kanallar

- Kimlik: **1** kanal (1 kayıt)
- Sağlam: **0** · Çalışmayan: **1**
- Kendi adresi bozuk ama otomatik yedekle kurtarılan: **0**
- ⚠️ Zırhlı listede kullanıcı adı/şifre içeren **1** adres var. Depo herkese açıksa bu hesap bilgileri herkes tarafından görülebilir.

<details><summary>Çalışmayan zırhlı kanallar</summary>

- GET PHP USERNAME IOS&PASSWORD SINETECH&TYPE M3U_PLUS — 1 kayıt · segment not media

</details>

## Gruplara göre sağlam kanallar

- **TR-DİĞER:** 159
- **TR-YEREL:** 129
- **TR-ULUSAL:** 53
- **TR-HABER:** 47
- **TR-MÜZİK:** 38
- **TR-DİNİ:** 22
- **TR-SPOR:** 17
- **TR-ÇOCUK:** 17
- **TR-BELGESEL:** 17
- **TR-SİNEMA:** 3

## En iyi 20 kanal (puan)

| Kanal | Puan | Sağlam kaynak | Çözünürlük | Açılış |
|---|---|---|---|---|
| TRT 1 | 100 | 6 | 1080p | 587 ms |
| Kanal D | 100 | 6 | 1080p | 576 ms |
| Show TV | 100 | 6 | 1080p | 179 ms |
| Star TV | 100 | 6 | 1080p | 563 ms |
| TV8 | 100 | 6 | 1080p | 211 ms |
| Beyaz TV | 100 | 6 | 1080p | 568 ms |
| 360 | 100 | 6 | 1080p | 463 ms |
| Teve2 | 100 | 6 | 1080p | 275 ms |
| TV8,5 | 100 | 6 | 1080p | 377 ms |
| TV4 | 100 | 6 | 1080p | 88 ms |
| A2 | 100 | 6 | 1080p | 878 ms |
| TRT Türk | 100 | 6 | 1080p | 920 ms |
| TRT Avaz | 100 | 6 | 1080p | 452 ms |
| TRT Kurdî | 100 | 6 | 1080p | 735 ms |
| TRT Arabi | 100 | 5 | 1080p | 585 ms |
| Show Max | 100 | 6 | 1080p | 896 ms |
| Show Türk | 100 | 1 | 1080p | 113 ms |
| Kanal 7 Avrupa | 100 | 6 | 1080p | 556 ms |
| TV 24 | 100 | 6 | 1080p | 190 ms |
| TYT Türk | 100 | 2 | 1080p | 622 ms |

## En verimli kaynaklar

- 238 sağlam · `https://raw.githubusercontent.com/YosemiteSam6/turkiye-iptv-m3u-m3u8/main/kanallar.m3u`
- 136 sağlam · `https://raw.githubusercontent.com/omerdenizhan/IPTV-M3U/main/m3u/turkiye-iptv-org.m3u`
- 111 sağlam · `https://raw.githubusercontent.com/raalbatros/iptv/HEAD/176.m3u`
- 62 sağlam · `https://raw.githubusercontent.com/hussobaba/tbrt_medya/HEAD/Huseyin_cvk_tv.m3u8`
- 45 sağlam · `https://raw.githubusercontent.com/MediaVizo/Premium1/HEAD/Giri%C5%9F%20Paketi.m3u8`
- 44 sağlam · `https://onureroz.com/indirmeler/turk/index.m3u`
- 41 sağlam · `https://raw.githubusercontent.com/Yusufdkci/iptv/main/liste.m3u`
- 33 sağlam · `https://raw.githubusercontent.com/braveheart1983/ataktv/HEAD/ataktv.m3u`
- 32 sağlam · `https://raw.githubusercontent.com/kodlama155-ctrl/tv/main/tr.m3u`
- 32 sağlam · `https://raw.githubusercontent.com/kodlama155-ctrl/tv/main/discovered.m3u`
- 31 sağlam · `https://raw.githubusercontent.com/BoranT-3000/PlayerM3U8/HEAD/data/master_all_channels.m3u8`
- 25 sağlam · `https://raw.githubusercontent.com/bugsfreeweb/LiveTVCollector/HEAD/BugsfreeStreams/Output/StreamLinks-TR.m3u`
- 24 sağlam · `https://raw.githubusercontent.com/ridvanseref37/tivi-rs-playlist/main/Tivi_RS_M3U_Listesi.m3u`
- 19 sağlam · `https://raw.githubusercontent.com/famelack/famelack-data/main/tv/countries/tr.json`
- 18 sağlam · `https://raw.githubusercontent.com/iptv-turk-tr/iptv/main/list.m3u`

## Ölü/engelli nedenleri

- http 403: 21
- segment http 403: 10
- timeout: 6
- http 404: 3
- segment http 401: 2
- variant http 500: 2
- too little data: 2
- segment not media: 1
- ffprobe: 1
- segment http 404: 1

_iptv-org ile zenginleştirilen kanal: 97_
