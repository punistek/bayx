# AkcagozTV — Otomatik Canlı TV Listesi

GitHub'da güncel Türkçe m3u listelerini **kendisi arar**, binlerce kanalı toplar,
**saçma / yabancı / film-dizi (VOD) olanları eler**, isimleri temizler, her yayını
**gerçekten test edip yalnızca canlı olanları** listeye ekler. Elle seçtiğin kanallar
(`zirhli.m3u`) hiç bozulmadan en üstte kalır. Tümü GitHub Actions'ta **6 saatte bir
otomatik** çalışır — senin bilgisayarın kapalıyken bile.

```
GitHub Actions (6 saatte bir)
   └─ update_list.py
        1) GitHub'da taze TR m3u depolarını ara  (sources.py)
        2) Kanalları topla + temizle + tekille     (parse.py / clean.py)
        3) Her yayını canlılık testinden geçir       (liveness.py)
        4) zirhli.m3u (korunan) + canlı bulunanlar → tr.m3u yaz
   └─ commit + push
        └─ tr.m3u'nun RAW linki → oynatıcı/uygulama buna abone olur
```

## Dosyalar

| Dosya | Ne işe yarar |
|---|---|
| `update_list.py` | Başlangıç noktası (çalıştırılan dosya) |
| `engine/config.py` | **Tüm ayarlar burada** — arama terimleri, yasaklı kelimeler, zaman aşımları |
| `engine/sources.py` | Kaynak bulma (GitHub arama + jsDelivr + sources.txt) |
| `engine/clean.py` | Kalite kapısı: eleme, isim temizleme, gruplama |
| `engine/liveness.py` | Canlılık testi (işin kalbi) |
| `engine/build.py` | Akışı yöneten orkestra |
| `zirhli.m3u` | **Senin elle seçtiğin kanallar** — asla test edilmez/silinmez, en üste eklenir |
| `tr.m3u` | Üretilen son liste (uygulamanın bağlanacağı dosya) |
| `sources.txt` | Elle ekstra m3u kaynağı eklemek istersen (her satır bir URL) |
| `RAPOR.md` | Her çalışmada üretilen özet (kaç kanal, hangi grup) |

## Kurulum (GitHub)

1. Bu klasörü olduğu gibi bir GitHub deposuna yükle (örn. `AkcagozTV_Canli`).
2. Depoda **Settings → Actions → General → Workflow permissions** → **Read and write permissions** seç.
3. Hepsi bu. İstersen **Actions** sekmesinden **Run workflow** ile elle de başlatabilirsin.
   Bundan sonra 6 saatte bir kendiliğinden çalışır.

> **GITHUB_TOKEN:** Workflow'un otomatik verdiği token yeterli. Daha çok kaynak taramak
> istersen kişisel bir token'ı `GH_TOKEN` secret'ı olarak ekleyebilirsin (şart değil).

## Uygulamaya / oynatıcıya bağlama

Bot `tr.m3u`'yu şu sabit adrese basar:

```
https://raw.githubusercontent.com/KULLANICI_ADIN/AkcagozTV_Canli/main/tr.m3u
```

Bu linki oynatıcına **playlist / m3u URL** olarak ekle. Uygulama belli aralıkla bu linki
yeniden çeker; bot ne güncellediyse onu görür. Bot ile uygulama birbirinden bağımsızdır:
bot bozulsa bile uygulama son iyi listeyi görmeye devam eder.

## Elle çalıştırma / test

```bash
pip install -r requirements.txt

python update_list.py              # tam otomasyon (ara + test + yaz)
python update_list.py --test-only  # arama yapma; mevcut tr.m3u'yu canlılıktan geçir
GITHUB_TOKEN=ghp_xxx python update_list.py   # daha geniş arama
```

## İnce ayar

`engine/config.py` içinden kod bilmeden ayar yapabilirsin:

- `SEARCH_TERMS` — GitHub'da aranacak terimler
- `YASAKLI_SET` — listeye alınmayacak kelimeler (yetişkin, film, yabancı...)
- `RECENT_DAYS` — kaç günden eski depolar atlansın
- `MAX_REPOS` / `MAX_TEST` — ne kadar geniş tarasın (büyük = yavaş ama bol)
- `TEST_TIMEOUT` / `THREADS_TEST` — canlılık testi hızı/titizliği
- `GROUP_RULES` — kanalların hangi gruba düşeceği

## Zırhlı liste (`zirhli.m3u`)

Senin güvendiğin, elle ayarladığın kanallar burada durur. Bot bu dosyaya **hiç
dokunmaz**: test etmez, ismini değiştirmez, silmez — `tr.m3u`'nun en üstüne aynen koyar.
Yeni güvendiğin bir kanal bulursan buraya ekle, gerisini bota bırak.

## Not

Bu araç yalnızca **halka açık** m3u kaynaklarını tarar ve canlılık testinden geçirir.
Başkasına ait abonelikli panel / şifreli hesap (`get.php?username=...`) kullanmaz.
Yalnızca erişim ve kullanım iznin olan yayınları ekle.
