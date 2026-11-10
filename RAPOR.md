# PuuStream IPTV Motoru — Güncelleme Raporu

**Tarih:** 11-11-2026 01:16 (TSİ) · **Test bölgesi:** github · **Süre:** 47 dk 48 sn

✅ **Yayınlandı.** Koruma: kontroller geçti

## Özet

| | |
|---|---|
| Sağlam kanal (en az 1 çalışan kaynak) | **305** |
| Yedek kaynağı olan kanal (≥2 sağlam) | 165 |
| tr.m3u otomatik bölüm kaydı | 470 |
| Test edilen adres | 1479 (derin/FFprobe: 477) |
| Sonuç | ✅ 718 sağlam · ⚠️ 26 kararsız · 🚫 181 engelli · ❌ 554 ölü |
| Karantinada (bu tur atlandı) | 355 |
| Kaynak listesi | 133/143 indirildi |
| Site çözücüleri (7 spor kaynağı) | 94 aday (sağlık testine tabi) |
| Aday (hafızadan geri çağrılan) | 1834 (19) |
| Türk listesi sayılan kaynak | 80 |
| Yabancı olduğu için indirilmeyen dosya | 1225 |
| Elenen | credential: 9105, banned: 1816, foreign: 8281 |

## Zırhlı kanallar

- Kimlik: **0** kanal (0 kayıt)
- Sağlam: **0** · Çalışmayan: **0**
- Kendi adresi bozuk ama otomatik yedekle kurtarılan: **0**

## Gruplara göre sağlam kanallar

- **TR-YEREL:** 92
- **TR-DİĞER:** 66
- **TR-ULUSAL:** 36
- **TR-HABER:** 28
- **TR-MÜZİK:** 27
- **TR-SPOR:** 20
- **TR-ÇOCUK:** 11
- **TR-DİNİ:** 11
- **TR-BELGESEL:** 10
- **TR-SİNEMA:** 4

## En iyi 20 kanal (puan)

| Kanal | Puan | Sağlam kaynak | Çözünürlük | Açılış |
|---|---|---|---|---|
| TRT 1 | 100 | 6 | 1080p | 743 ms |
| Kanal D | 100 | 6 | 1080p | 854 ms |
| Show TV | 100 | 6 | 1080p | 236 ms |
| Star TV | 100 | 6 | 1080p | 897 ms |
| NOW | 100 | 5 | 1080p | 470 ms |
| TV8 | 100 | 3 | 1080p | 277 ms |
| Beyaz TV | 100 | 5 | 1080p | 838 ms |
| 360 | 100 | 5 | 1080p | 775 ms |
| Teve2 | 100 | 6 | 1080p | 853 ms |
| A2 | 100 | 5 | 1080p | 457 ms |
| TRT Türk | 100 | 4 | 1080p | 355 ms |
| TRT Avaz | 100 | 3 | 1080p | 720 ms |
| TRT Kurdî | 100 | 4 | 1080p | 445 ms |
| TRT Arabi | 100 | 3 | 1080p | 917 ms |
| Show Max | 100 | 4 | 1080p | 315 ms |
| Kanal 7 Avrupa | 100 | 4 | 1080p | 590 ms |
| TV 24 | 100 | 6 | 1080p | 634 ms |
| TYT Türk | 100 | 1 | 1080p | 783 ms |
| Vav TV | 100 | 2 | 1080p | 571 ms |
| Meltem TV | 100 | 4 | 1080p | 840 ms |

## En verimli kaynaklar

- 267 sağlam · `https://raw.githubusercontent.com/YosemiteSam6/turkiye-iptv-m3u-m3u8/main/kanallar.m3u`
- 142 sağlam · `https://raw.githubusercontent.com/iptv-org/iptv/master/streams/tr.m3u`
- 58 sağlam · `https://raw.githubusercontent.com/BoranT-3000/PlayerM3U8/HEAD/data/master_all_channels.m3u8`
- 50 sağlam · `https://raw.githubusercontent.com/Yusufdkci/iptv/main/liste.m3u`
- 32 sağlam · `https://raw.githubusercontent.com/ridvanseref37/tivi-rs-playlist/main/Tivi_RS_M3U_Listesi.m3u`
- 21 sağlam · `https://raw.githubusercontent.com/allthethingsyouhavechased-ui/tv-liste/main/k.m3u`
- 17 sağlam · `https://raw.githubusercontent.com/eakcabag/canli-tv/main/ulusal.m3u`
- 16 sağlam · `site:andro`
- 15 sağlam · `https://raw.githubusercontent.com/emrecemal/my-iptv-playlist/main/playlist.m3u`
- 14 sağlam · `https://raw.githubusercontent.com/ikiartiiki/deneme/HEAD/turk.m3u8`
- 10 sağlam · `https://raw.githubusercontent.com/qazim/IPTV/main/tr.m3u`
- 10 sağlam · `https://raw.githubusercontent.com/stagh345/iptv-az-tr-ru/main/docs/index.m3u`
- 9 sağlam · `https://raw.githubusercontent.com/Walid533112/Sony/HEAD/Sony.m3u8`
- 9 sağlam · `https://raw.githubusercontent.com/hayatiptv/iptv/HEAD/index.m3u`
- 8 sağlam · `https://raw.githubusercontent.com/lensphotostudio/turk-iptv/main/kanallar.m3u`

## Ölü/engelli nedenleri

- http 404: 258
- connect: 169
- http 403: 130
- timeout: 64
- segment http 401: 22
- ffprobe: 17
- http 401: 16
- http 500: 15
- segment http 403: 10
- not media: 7
- vod: 5
- segment not media: 4

_iptv-org ile zenginleştirilen kanal: 97_
