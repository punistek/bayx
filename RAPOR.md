# PuuStream IPTV Motoru — Güncelleme Raporu

**Tarih:** 18-11-2026 10:29 (TSİ) · **Test bölgesi:** github · **Süre:** 8 dk 25 sn

✅ **Yayınlandı.** Koruma: kontroller geçti

## Özet

| | |
|---|---|
| Sağlam kanal (en az 1 çalışan kaynak) | **502** |
| Yedek kaynağı olan kanal (≥2 sağlam) | 199 |
| tr.m3u otomatik bölüm kaydı | 701 |
| Test edilen adres | 1743 (derin/FFprobe: 500) |
| Sonuç | ✅ 1245 sağlam · ⚠️ 38 kararsız · 🚫 239 engelli · ❌ 221 ölü |
| Karantinada (bu tur atlandı) | 1041 |
| Kaynak listesi | 233/242 indirildi |
| Site çözücüleri (7 spor kaynağı) | 94 aday (sağlık testine tabi) |
| Aday (hafızadan geri çağrılan) | 2783 (579) |
| Resmî site çözücüleri · JSON veritabanı · kardeş sunucu | 11 · 150 · 144 aday |
| Türk listesi sayılan kaynak | 177 |
| Yabancı olduğu için indirilmeyen dosya | 2453 |
| Elenen | credential: 46804, paid: 1512, banned: 7832, foreign: 8612 |

## Zırhlı kanallar

- Kimlik: **1** kanal (1 kayıt)
- Sağlam: **0** · Çalışmayan: **1**
- Kendi adresi bozuk ama otomatik yedekle kurtarılan: **0**
- ⚠️ Zırhlı listede kullanıcı adı/şifre içeren **1** adres var. Depo herkese açıksa bu hesap bilgileri herkes tarafından görülebilir.

<details><summary>Çalışmayan zırhlı kanallar</summary>

- GET PHP USERNAME IOS&PASSWORD SINETECH&TYPE M3U_PLUS — 1 kayıt · segment not media

</details>

## Gruplara göre sağlam kanallar

- **TR-DİĞER:** 157
- **TR-YEREL:** 129
- **TR-ULUSAL:** 54
- **TR-HABER:** 47
- **TR-MÜZİK:** 39
- **TR-DİNİ:** 22
- **TR-SPOR:** 17
- **TR-ÇOCUK:** 17
- **TR-BELGESEL:** 17
- **TR-SİNEMA:** 3

## En iyi 20 kanal (puan)

| Kanal | Puan | Sağlam kaynak | Çözünürlük | Açılış |
|---|---|---|---|---|
| TRT 1 | 100 | 6 | 1080p | 689 ms |
| Kanal D | 100 | 6 | 1080p | 420 ms |
| Show TV | 100 | 6 | 1080p | 203 ms |
| Star TV | 100 | 6 | 1080p | 429 ms |
| TV8 | 100 | 6 | 1080p | 229 ms |
| Beyaz TV | 100 | 6 | 1080p | 529 ms |
| 360 | 100 | 6 | 1080p | 769 ms |
| Teve2 | 100 | 6 | 1080p | 270 ms |
| TV8,5 | 100 | 6 | 1080p | 347 ms |
| TV4 | 100 | 6 | 1080p | 109 ms |
| A2 | 100 | 6 | 1080p | 805 ms |
| TRT Türk | 100 | 6 | 1440p | 158 ms |
| TRT Avaz | 100 | 6 | 1080p | 797 ms |
| TRT Kurdî | 100 | 6 | 1080p | 346 ms |
| TRT Arabi | 100 | 5 | 1080p | 565 ms |
| Show Max | 100 | 6 | 1080p | 921 ms |
| Show Türk | 100 | 1 | 1080p | 202 ms |
| Kanal 7 Avrupa | 100 | 6 | 1080p | 460 ms |
| TV 24 | 100 | 6 | 1080p | 160 ms |
| TYT Türk | 100 | 2 | 1080p | 655 ms |

## En verimli kaynaklar

- 242 sağlam · `https://raw.githubusercontent.com/YosemiteSam6/turkiye-iptv-m3u-m3u8/main/kanallar.m3u`
- 136 sağlam · `https://raw.githubusercontent.com/omerdenizhan/IPTV-M3U/main/m3u/turkiye-iptv-org.m3u`
- 108 sağlam · `https://raw.githubusercontent.com/raalbatros/iptv/HEAD/176.m3u`
- 62 sağlam · `https://raw.githubusercontent.com/hussobaba/tbrt_medya/HEAD/Huseyin_cvk_tv.m3u8`
- 45 sağlam · `https://onureroz.com/indirmeler/turk/index.m3u`
- 45 sağlam · `https://raw.githubusercontent.com/MediaVizo/Premium1/HEAD/Giri%C5%9F%20Paketi.m3u8`
- 41 sağlam · `https://raw.githubusercontent.com/Yusufdkci/iptv/main/liste.m3u`
- 33 sağlam · `https://raw.githubusercontent.com/kodlama155-ctrl/tv/main/discovered.m3u`
- 33 sağlam · `https://raw.githubusercontent.com/braveheart1983/ataktv/HEAD/ataktv.m3u`
- 32 sağlam · `https://raw.githubusercontent.com/kodlama155-ctrl/tv/main/tr.m3u`
- 29 sağlam · `https://raw.githubusercontent.com/BoranT-3000/PlayerM3U8/HEAD/data/master_all_channels.m3u8`
- 25 sağlam · `https://raw.githubusercontent.com/bugsfreeweb/LiveTVCollector/HEAD/BugsfreeStreams/Output/StreamLinks-TR.m3u`
- 24 sağlam · `https://raw.githubusercontent.com/ridvanseref37/tivi-rs-playlist/main/Tivi_RS_M3U_Listesi.m3u`
- 20 sağlam · `https://raw.githubusercontent.com/iptv-turk-tr/iptv/main/list.m3u`
- 19 sağlam · `https://raw.githubusercontent.com/famelack/famelack-data/main/tv/countries/tr.json`

## Ölü/engelli nedenleri

- http 403: 214
- timeout: 78
- radio: 49
- http 404: 37
- connect: 31
- segment http 401: 11
- http 401: 9
- segment http 403: 5
- variant http 500: 4
- ffprobe: 4
- segment http 404: 3
- vod: 3

_iptv-org ile zenginleştirilen kanal: 97_
