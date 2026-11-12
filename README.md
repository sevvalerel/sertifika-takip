# Sertifika Takip Listesi

Müşterilerin SSL sertifikalarının bitiş tarihlerini takip eden basit bir Django uygulaması.

- Sertifikalar (alan adı, müşteri adı, bitiş tarihi) **Django admin** panelinden eklenip düzenlenir.
- Ana sayfada tüm sertifikalar **bitiş tarihine göre** sıralanır. Her satırda **kalan gün** ve **durum** gösterilir: *Süresi dolmuş*, *Yakında dolacak* ya da *Geçerli*.

Tek bağımlılık Django 5.2 LTS, veritabanı SQLite.

## Kurulum ve çalıştırma

Gereksinim: Python 3.11 veya üzeri (Python 3.12 ile geliştirildi).

**Windows (PowerShell)**

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

> `.\.venv\Scripts\Activate.ps1` betik çalıştırma kısıtlamasına takılabilir. Yukarıdaki komutlar sanal ortamı etkinleştirmeden çalışır.

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Kullanım

| Adres | Ne var |
|---|---|
| http://127.0.0.1:8000/ | Sertifika listesi |
| http://127.0.0.1:8000/admin/ | Kayıt ekleme ve düzenleme (`createsuperuser` ile oluşturduğun kullanıcıyla giriş yapılır) |

Admin'de tarih **gg/aa/yyyy** biçiminde girilir, örneğin `13/12/2026`. `2026-12-13` biçimi de kabul edilir. Noktalı biçim (`13.12.2026`) **kabul edilmez**. Liste sayfası da tarihleri aynı biçimde gösterir.

## Testler

```bash
python manage.py test        # Windows: .\.venv\Scripts\python.exe manage.py test
```

21 test var. Hepsi [certificates/tests.py](certificates/tests.py) dosyasında ve "bugün" testlerde sabit bir tarihe (12/11/2026) bağlanır.

| Grup | Kapsam |
|---|---|
| Durum hesabı (8) | Her durumdan bir örnek ve iki sınırın iki yanı: **−1 / 0** (dolmuş / yakında) ve **30 / 31** (yakında / geçerli). Eşik sabiti değiştirilince kuralın ona uyduğu da test edilir. |
| Kalan gün (3) | Negatif değer, yıl geçişi, artık yıl |
| Model ve admin (6) | Alan adının küçük harfe çevrilmesi, büyük/küçük harf farkıyla tekrar kayıt (admin formunda 500 yerine form hatası), düzenlenen kaydın kendisiyle çakışmaması, admin sayacı ve başlığı |
| Liste sayfası (4) | Sıralama ve durum etiketleri, aynı tarihteki kayıtların alan adına göre sırası, boş liste mesajı, saat dilimi (UTC 22:30, İstanbul'da ertesi gün) |

Kritik testler, kod bilerek bozularak denendi. Örneğin `<=` yerine `<` yazılınca yalnızca sınır testleri kırıldı.

## Varsayımlar

Ödevde belirtilmeyen noktalar için verilen kararlar:

| Konu | Karar | Gerekçe |
|---|---|---|
| Durum kuralı | kalan **< 0** → Süresi dolmuş · **0–30** → Yakında dolacak · **≥ 31** → Geçerli | |
| Bitiş günü (kalan = 0) | **Yakında dolacak** | RFC 5280'e göre geçerlilik süresi bitiş anını da kapsar ("notAfter, inclusive"). Sertifika bitiş günü boyunca hâlâ geçerlidir. |
| "Yakında" eşiği | **30 gün, sınır dahil** | Tek bir sabitte duruyor: `EXPIRING_SOON_DAYS` ([status.py](certificates/status.py)) |
| "Bugün" | `Europe/Istanbul` saat dilimine göre (`timezone.localdate()`) | UTC kullanılsaydı Türkiye'de 00:00–03:00 arasında sonuçlar bir gün kayardı. |
| Saat bilgisi | Yalnızca tarih saklanır (`DateField`) | Gerçek sertifikanın bitişi bir saat de içerir ve bu saat sağlayıcıya göre değişir. DigiCert gün sonunu (23:59:59 UTC) kullanır. Let's Encrypt'te ise bitiş saati sertifikanın verildiği ana bağlıdır. Yani sertifika bitiş gününün herhangi bir saatinde sona erebilir. Uygulama bitiş gününün tamamını "Yakında dolacak" sayar. Basitlik için bu saat farkı kabul edildi. |
| Alan adı | **Tekil**. Kaydederken boşluklar kırpılır ve küçük harfe çevrilir. | Aynı alan adı için tek kayıt tutulur, yenilemede tarih güncellenir. `Example.com` ile `example.com` aynı kayıt sayılır. |
| Alan adı biçimi | Doğrulanmaz | `*.example.com` gibi wildcard sertifikaların da girilebilmesi için. Karşılığında hatalı bir metin de girilebilir. |
| Müşteri | Düz metin, ayrı bir tablo değil | Ödev yalnızca "müşteri adı" istiyor. |
| Durum | Veritabanına yazılmaz, her istekte hesaplanır | Durum zamanla kendiliğinden değişir. Saklansaydı bayatlardı. |
| Sıralama | Bitiş tarihi, eşitse alan adı | Süresi dolmuşlar ve en acil olanlar en üstte görünür. |
| Süresi dolmuş kayıtta kalan gün | Negatif gösterilir (örn. `-5`) | |

## Bilinçli eklemeler

Planda olmayan ama çalışırken eklenen şeyler:

- **Liste sayfasında sade bir koyu tema** ve durum rozetleri. CSS template'in içinde, dış bağımlılık yok.
- **Tarih biçimi `gg/aa/yyyy`:** Sayfada görünen tarih admin'e olduğu gibi yazılabilsin diye.
- **Admin'de "4 sertifika":** Django varsayılan olarak "4 sertifikalar" yazıyor. Türkçede sayıdan sonra isim tekil kalır. Yalnızca bu model için [pagination.html](certificates/templates/admin/certificates/certificate/pagination.html) şablonu ezildi.
- **Admin başlığı:** "Django yönetimi" yerine "Sertifika Takip Yönetimi"
- **`SECRET_KEY` ortam değişkeninden okunur** (`DJANGO_SECRET_KEY`). Değişken yoksa yerel geliştirme anahtarı kullanılır.

## Canlıya alma öncesi yapılması gerekenler

Ödev canlıya almayı kapsamıyor. Uygulama şu haliyle yalnızca yerel geliştirme içindir. Canlıya alınsaydı yapılması gerekenler:

- **Yeni bir `SECRET_KEY`** üretip `DJANGO_SECRET_KEY` ile vermek. Koddaki varsayılan anahtar git geçmişinde açıktır, asla kullanılmamalı.
- `DEBUG = False` ve `ALLOWED_HOSTS` içine yalnızca gerçek alan adını yazmak.
- **Liste sayfasını korumak** (`@login_required` ya da iç ağ kısıtı). Şu an herkes müşteri adlarını ve bitiş tarihlerini görebilir.
- HTTPS ayarları: `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, HSTS
- Admin için giriş denemesi sınırı ve güçlü şifreler, mümkünse iki aşamalı doğrulama
- `runserver` yerine gunicorn/uwsgi ve önünde bir ters vekil sunucu. Statik dosyalar için `collectstatic`.
- SQLite yerine (ya da yanında) yedekleme planı. Bağımlılıkların düzenli güncellenmesi.

Kontrol için: `python manage.py check --deploy`

## AI ile çalışma notu

**İşe nasıl başladın, AI'a ilk ne verdin?**

_(yazılacak)_

**AI'ın yazdığı kodun doğru çalıştığını nasıl kontrol ettin?**

_(yazılacak)_

**Testlerin hangi durumları kapsaması gerektiğine nasıl karar verdin?**

_(yazılacak)_

**AI'ın yanlış yaptığı ya da yönlendirmen gereken bir an oldu mu, ne yaptın?**

_(yazılacak)_

## AI oturum kayıtları

[ai-log/](ai-log/) klasöründe Claude Code oturumlarının `/export` çıktıları var. Düzenlenmeden, olduğu gibi eklendi.
