# InspectionApp — Mevcut Mimari Analizi

> Bu doküman, gelişmiş (v2) bir sürüm tasarlamadan önce referans almak üzere mevcut uygulamanın yapısını, veri modelini ve bilinen teknik borcunu özetler. Analiz, `database.db` üzerinde çalıştırılan canlı şema sorgularına ve kod taramasına dayanır (2026-06-25 itibarıyla).

## 1. Uygulama ne işe yarıyor

Saha ekipmanlarının (yangın tüpü, SCBA/solunum cihazı, EEBA, sabit/kişisel gaz dedektörü) **QR/etiket ile takibi, periyodik denetim kaydı ve PDF/etiket üretimi** yapan bir Flask web uygulaması. Gerçek üretim verisiyle aktif kullanılıyor — `scba_units` 953, `cylinders` 928, `regulators` 925, `cards` (üretilmiş etiket) 208, `eebas` 50, `area_gas_monitors` 33 kayıt içeriyor.

## 2. Teknoloji yığını

| Katman | Teknoloji |
|---|---|
| Backend | Flask 3.x (saf, Blueprint'lerle kısmen modülerleştirilmiş) |
| Veritabanı | SQLite (`database.db`), ham `sqlite3` modülü — ORM yok, migration aracı yok |
| Kimlik doğrulama | Flask `session` + `bcrypt` (şifre hash), rol bazlı dekoratörler |
| Frontend | Jinja2 template'leri + (muhtemelen) Bootstrap, masaüstü/mobil için **ayrı** template dosyaları |
| PDF/Etiket | `reportlab`, `qrcode` |
| Excel import/export | `pandas` |
| Dış entegrasyon | Google BigQuery'e tek yönlü veri aktarımı (`upload_to_bigquery.py`, manuel çalıştırılan script) |
| Deploy | Docker + gunicorn (yeni eklendi), Easypanel hedefli |

`requirements.txt` içeriği: Flask, gunicorn, pandas, qrcode[pil], reportlab, bcrypt, python-dateutil, google-cloud-bigquery, db-dtypes.

## 3. Proje yapısı

```
mysite/
├── app.py                     # 3922 satır — MONOLİTİK çekirdek (auth, products, scba, fire_extinguishers, pdf/etiket üretimi)
├── auth_utils.py              # login_required / role_required dekoratörleri
├── utils.py                   # tek bir yardımcı fonksiyon (normalize_result)
├── config.py                  # KULLANILMIYOR — app.py kendi secret_key'ini ayarlıyor, Config sınıfı import edilmiyor
├── area_gas_monitor/          # Blueprint: sabit gaz dedektörleri (harita görünümü dahil)
├── eeba/                      # Blueprint: EEBA ekipmanları (Excel toplu yükleme destekli)
├── personal_gas_monitor/      # Blueprint: kişisel gaz dedektörleri
├── new_module/                # Blueprint — sadece örnek/iskelet, gerçek işlevi yok
├── gps_module/                # Blueprint — TANIMLI AMA app.py'de hiç register edilmemiş (ölü kod)
├── blueprints/fire_extinguisher.py  # Boş/kullanılmayan dosya — yangın tüpü mantığı asıl app.py'de
├── templates/                 # 54 html — çoğu özellik için masaüstü+mobil ayrı şablon
├── static/                    # logo, ikonlar, manifest.json (PWA)
├── scba_tablolari.py, scba_tag_number.py, init_eebas_db.py, sync_scba_units_to_cylinders_and_regulators.py, tagcheck.py
│                               # tek seferlik / bakım amaçlı CLI scriptleri (web uygulamasının parçası değil)
└── upload_to_bigquery.py      # manuel BigQuery export scripti
```

## 4. Mimari desen

**Kısmen modüler monolit.** 4 ekipman tipi (gaz dedektörleri + EEBA) Blueprint'lere ayrılmış; ama en eski/en büyük 3 modül (genel "products", SCBA, yangın tüpü) hâlâ tek `app.py` dosyasında, 3900+ satır halinde. Aynı CRUD + denetim + PDF/QR deseni her ekipman tipi için **ayrı ayrı, kod tekrarıyla** yeniden yazılmış — ortak bir "equipment" abstraction'ı yok.

Route sayısı: **94** (test edildi, `flask url_map` üzerinden doğrulandı).

## 5. Veritabanı şeması (canlı `database.db`'den)

18 tablo var. Üç farklı "ekipman" data modeli paterni dikkat çekiyor:

### Genel ürün sistemi (eski/az kullanılan)
- `products` (11 kolon) — sadece **1 satır**, `brands`(2), `product_types`(29), `companies`(7)
- `inspections` (6 kolon, 2 satır), `assignments` (7 kolon, 1 satır)
- Bu tablolar genel bir "herhangi bir ürünü takip et" sistemi olarak tasarlanmış ama pratikte kullanılmamış — her ekipman tipi kendi özel tablosuna kaymış.

### SCBA (en yoğun kullanılan modül)
- `scba_units` (12 kolon, **953 satır**) — eski/birincil tablo
- `cylinders` (8 kolon, 928), `regulators` (6 kolon, 925), `scba_assemblies` (8 kolon, 8) — `scba_tablolari.py` ile sonradan eklenmiş **paralel** bir veri modeli (cylinder+regulator ayrımı)
- `scba_inspections` (10 kolon, 30 satır)
- **Not:** `scba_units` ve `cylinders/regulators/scba_assemblies` aynı varlığı iki farklı şekilde modelliyor — muhtemelen yarım kalmış bir migrasyon.

### Yangın tüpü
- `fire_extinguishers` (17 kolon, 3 satır), `fire_extinguisher_inspections` (9 kolon, 22 satır)

### Diğer ekipmanlar (Blueprint'li, en temiz şema)
- `eebas` (25 kolon, 50 satır) — trigger ile `updated_at` otomatik güncelleniyor, en iyi tasarlanmış tablo
- `area_gas_monitors` (17 kolon, 33 satır) — GPS/harita alanları var (`latitude/longitude` VE `gps_latitude/gps_longitude` — **kolon tekrarı**)
- `personal_gas_monitors` (14 kolon, 14 satır)

### Auth
- `auth_users` (id, username, full_name, role, password-hash) — **gerçek login tablosu**
- `users` (badge_number, full_name, role, password) — **ayrı, kafa karıştırıcı isimde ikinci bir tablo**, ürün atamalarında "badge_number" referansı için kullanılıyor. İki farklı kullanıcı kavramı var.
- `cards` (id, tag, qr_url, 208 satır) — üretilen QR etiketlerin kaydı

## 6. Kimlik doğrulama & yetkilendirme

- Session tabanlı login (`/login`), şifreler `bcrypt` ile hashlenmiş.
- 3 rol: `admin`, `inspector`, `viewer` — `@role_required('admin', 'inspector')` dekoratörüyle route bazlı kontrol.
- Şu an üretim DB'sinde **sadece 1 auth_users kaydı** (tek admin).
- `SECRET_KEY` artık env var'dan okunuyor (deploy hazırlığı kapsamında düzeltildi), öncesinde hardcoded'dı.

## 7. Öne çıkan iş akışları

1. **Tag/QR ile hızlı denetim:** Her ekipmana benzersiz tag basılır (`cards` tablosu) → sahada QR okutulur veya tag manuel girilir → ilgili denetim formu açılır → sonuç kaydedilir.
2. **Masaüstü/mobil ayrımı:** `request.user_agent` string'inde "android/iphone/ipad/mobile" araması yapılarak (`app.py:3470`) iki ayrı template render ediliyor (örn. `inspect_fire_extinguisher.html` vs `..._mobile.html`). Tek bir responsive template yerine kod ve bakım ikiye katlanmış.
3. **PDF/etiket üretimi:** `reportlab` ile toplu QR kart sayfaları (`OUTPUT_FOLDER/cards_page_N.pdf`) ve atama/özet raporları bellekte (`BytesIO`) üretiliyor.
4. **Excel toplu yükleme:** En azından EEBA modülü (`eeba/routes.py`) ve SCBA (`upload_scba`) `.xlsx` toplu içe aktarma destekliyor (`pandas`).
5. **BigQuery senkronizasyonu:** Sadece `fire_extinguishers` tablosu için, manuel/cron ile tetiklenen tek yönlü export.

## 8. Bilinen teknik borç (v2 tasarımı için girdi)

| # | Sorun | Etki |
|---|---|---|
| 1 | `app.py` 3922 satır, tek dosyada 3 farklı ekipman domaini | Bakım/okunabilirlik çok düşük |
| 2 | Aynı CRUD+inspect+PDF deseni 4+ kez kopyalanmış (ortak "Equipment" abstraction yok) | Yeni ekipman tipi eklemek = baştan yazmak |
| 3 | SCBA için iki paralel veri modeli (`scba_units` vs `cylinders/regulators/scba_assemblies`) | Veri tutarsızlığı riski, hangi tablo "doğru kaynak" belirsiz |
| 4 | İki farklı kullanıcı tablosu (`users` vs `auth_users`) | Kavramsal karışıklık |
| 5 | `products`/`inspections`/`assignments` tabloları neredeyse boş, ölü genel sistem | Gereksiz kod yolu |
| 6 | Masaüstü/mobil için ayrı template+route (user-agent sniffing) | Responsive CSS yerine kod tekrarı |
| 7 | `gps_module` register edilmemiş, `new_module` sadece iskelet | Ölü kod |
| 8 | ORM yok, ham SQL string'leri her yerde (yine de parametreli sorgular kullanılmış, SQL injection bulunamadı — bu iyi) | Şema değişikliği = elle her query'i bulup düzeltmek |
| 9 | Migration sistemi yok — şema değişiklikleri tek seferlik script'lerle (`eksiktablo.py` vb., bu temizlikte silindi) yapılmış | Şema geçmişi takip edilemiyor |
| 10 | Test yok (unit/integration) | Regresyon riski yüksek |
| 11 | `config.py` (Config sınıfı) tanımlı ama hiç kullanılmıyor | Kafa karışıklığı |
| 12 | Statik dosya yükleme (`UPLOAD_FOLDER`) yok, tüm PDF'ler bellekte üretiliyor | Büyük raporlarda bellek baskısı olabilir |
| 13 | `area_gas_monitors` tablosunda yinelenen koordinat kolonları (`latitude/longitude` + `gps_latitude/gps_longitude`) | Şema temizliği gerekiyor |

## 9. Olumlu bulgular (korunmaya değer)

- SQL sorguları tutarlı şekilde **parametreli** (`?` placeholder) — SQL injection riski tespit edilmedi.
- `bcrypt` ile şifre hashleme doğru yapılmış.
- Rol bazlı erişim kontrolü dekoratör pattern'iyle tutarlı uygulanmış.
- EEBA modülü (trigger'lı `updated_at`, indeksler, CHECK constraint) — şema kalitesi en yüksek modül, v2'de referans alınabilir.
- Gerçek, aktif kullanılan üretim verisi var — v2 tasarımı "boş kağıt" değil, gerçek veri taşıma (migration) ihtiyacı gözetilerek yapılmalı.

## 10. v2 için üzerinde durulacak temel kararlar

Bir sonraki konuşmada birlikte netleştirilecek başlıklar:
- Tek "Equipment" tablosu + tip-bazlı esnek alanlar (EAV/JSON) mı, yoksa her tipin kendi tablosu ama ortak bir servis katmanı mı?
- ORM'e geçiş (SQLAlchemy) ve Alembic ile migration
- Masaüstü/mobil için tek responsive template
- SCBA'daki iki paralel modelin birleştirilmesi ve veri taşıma planı
- `users` / `auth_users` birleşimi
- Test altyapısı (pytest + fixture DB)
