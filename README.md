# Stream Monitor Pro - Chaturbate Edition

⚠️ **UYARI: Bu yazılım sadece eğitim amaçlıdır. İzinsiz kayıt yapmak yasadışıdır ve platform kurallarını ihlal eder. Kullanım sorumluluğu size aittir.**

## ✨ Özellikler

- 🎥 **Otomatik Kayıt**: Yayıncı online olduğunda otomatik kayıt başlar
- 📸 **Canlı Snapshot**: FFmpeg ile yayından gerçek kesit alınır
- 🌐 **Modern Web Arayüzü**: Responsive, görsel kart/liste görünümü
- 🔄 **Akıllı Sıralama**: Online yayıncılar üstte, offline olanlar altta
- 📊 **Gerçek Zamanlı İstatistikler**: Anlık durum takibi
- 🎬 **Video Yönetimi**: İzle, indir, sil - tümü web arayüzünde

## 📋 Gereksinimler

- Python 3.8+
- FFmpeg (sistem PATH'inde)
- requests kütüphanesi
- dnspython kütüphanesi
- Flask

## 🚀 Kurulum

### 1. FFmpeg Kurulumu

**Windows:**
1. https://ffmpeg.org/download.html adresinden indir
2. ZIP'i aç ve `bin` klasörünü PATH'e ekle
3. Kontrol: `ffmpeg -version`

### 2. Python Paketlerini Yükle
```bash
pip install -r requirements.txt
```

### 3. Klasör Yapısını Oluştur
```bash
python setup_static_folders.py
```

Bu komut şu klasörleri oluşturur:
```
project/
├── static/
│   ├── logos/
│   │   └── chaturbate.png    ← Site logosunu buraya koy
│   └── users/
│       └── {username}.jpg    ← FFmpeg snapshot'lar (otomatik)
├── recordings/
│   └── {username}/
│       └── *.mp4
├── Downloader.py
├── web_interface.py
├── chaturbate_implementation.py
└── config.json
```

### 4. Site Logosunu Ekle
`static/logos/chaturbate.png` dosyasını projeye ekleyin. Bu logo profil kartlarında görünecek.

## 🎯 Kullanım

### Web Arayüzü (Önerilen)
```bash
python web_interface.py
```

Tarayıcıda açın: `http://localhost:5000`

**Özellikler:**
- ➕ Yayıncı ekle/çıkar
- ▶️ İzlemeyi başlat/durdur
- 🔄 Kart/Liste görünüm değiştir
- 📹 Kayıtları izle/indir/sil
- 📊 Gerçek zamanlı istatistikler

### Konsol Arayüzü
```bash
python Downloader.py
```

**Komutlar:**
```
add <username> CB     - Yayıncı ekle
remove <username> CB  - Yayıncı çıkar
start <username> CB   - İzlemeyi başlat
start *               - Tümünü başlat
stop <username> CB    - İzlemeyi durdur
stop *                - Tümünü durdur
status                - Durum göster
files                 - Kayıtları listele
help                  - Yardım
quit                  - Çıkış
```

## 📸 Snapshot Sistemi

FFmpeg otomatik olarak yayından bir frame yakalayıp `static/users/{username}.jpg` olarak kaydeder:

- ✅ Kayıt başladığında otomatik çalışır
- ✅ 400px genişlik, yüksek kalite
- ✅ 1 saat cache (gereksiz snapshot önlenir)
- ✅ Web arayüzünde avatar olarak görünür
- ✅ Fallback: Chaturbate thumbnail'i

## 🎨 Web Arayüzü

### Dashboard
- **Kart Görünümü**: Modern profil kartları (varsayılan)
- **Liste Görünümü**: Kompakt horizontal liste
- **Akıllı Sıralama**: Online → Offline
- **Gerçek Fotoğraflar**: FFmpeg snapshot'ları
- **Site Logosu**: Sağ üst köşede Chaturbate logosu
- **Profil Linki**: Kullanıcı adına tıkla → Canlı yayın

### Video Yönetimi
- Video player ile önizleme
- İndirme ve silme işlemleri
- Kullanıcı bazında filtreleme
- Dosya boyutu ve tarih bilgisi

## 📁 Dosya Yapısı

### Kayıtlar
```
recordings/
├── username1/
│   ├── CB_username1_20241015_143052.mp4
│   └── CB_username1_20241015_180234.mp4
└── username2/
    └── CB_username2_20241015_145612.mp4
```

### Snapshot'lar
```
static/users/
├── username1.jpg
├── username2.jpg
└── username3.jpg
```

### Logolar
```
static/logos/
└── chaturbate.png
```

## ⚙️ Ayarlar

### Kontrol Aralığı
`StreamMonitor(check_interval=60)` → Varsayılan 60 saniye

### Snapshot Boyutu
`'-vf', 'scale=400:-1'` → 400px genişlik

### Snapshot Cache
`file_age < 3600` → 1 saat

## 🔧 Sorun Giderme

**FFmpeg Bulunamadı:**
```bash
ffmpeg -version  # Kontrol et
# PATH'e eklendiğinden emin ol
```

**Snapshot Alınamıyor:**
- Stream URL'i kontrol et
- FFmpeg timeout (10 saniye)
- Manuel test: `ffmpeg -i {stream_url} -vframes 1 test.jpg`

**Stream URL Alınamıyor:**
- Yayıncı online mı kontrol et
- Kullanıcı adını doğru yazdığından emin ol
- API testi: `python chaturbate_implementation.py`

**Web Arayüzü Açılmıyor:**
```bash
# Port kontrolü
netstat -ano | findstr :5000

# Farklı port dene
python web_interface.py --port 8080
```

## 📊 İstatistikler

Web arayüzü gerçek zamanlı şu verileri gösterir:
- Toplam yayıncı sayısı
- Online yayıncı sayısı
- Aktif kayıt sayısı
- Toplam kayıt dosyası sayısı

Her yayıncı için:
- Online/Offline durumu
- Kayıt durumu (🔴 Kaydediliyor)
- Kayıt süresi
- Kontrol sayısı

## 🔐 Güvenlik

1. **Yasal Uyarı**: İzinsiz kayıt yapmak yasadışıdır
2. **Gizlilik**: Kayıtları paylaşmayın
3. **Platform Kuralları**: Chaturbate ToS'u ihlal eder
4. **Sorumluluk**: Kullanım sorumluluğu size aittir

## 🎓 Eğitim Amaçlı

Bu proje yalnızca:
- FFmpeg kullanımı
- Flask web geliştirme
- Threading ve async işlemler
- Video streaming teknolojileri
konularında eğitim amaçlıdır.

## 📝 Lisans

Eğitim amaçlı proje. MIT License.

## 🐛 Bug Raporu

Sorun yaşarsanız:
1. FFmpeg versiyonunu kontrol edin
2. Python versiyonunu kontrol edin
3. Log dosyalarını inceleyin
4. Console output'u kontrol edin

## 🚀 Gelecek Özellikler

- [ ] Çoklu site desteği (Stripchat, BongaCams, vb.)
- [ ] Telegram/Discord bildirimleri
- [ ] Video kalite seçimi
- [ ] Otomatik backup
- [ ] API endpoint'leri
- [ ] Mobile responsive iyileştirmeleri

---

**Önemli Not**: Bu yazılım sadece eğitim amaçlıdır. Kullanımdan kaynaklanan yasal sorumluluk kullanıcıya aittir.