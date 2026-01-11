# 🚁 ARES - Multi-Agent Tactical Command System

Yapay zeka destekli otonom İHA komuta ve kontrol sistemi. Fixed-wing ArduPlane SITL simülasyonu ile entegre multi-agent mimarisi.

## 🎯 Özellikler

- **Multi-Agent Yapısı**: Commander (Gemini AI) → Worker (A*) → Safety Validator → Doer
- **Gerçek Zamanlı Simülasyon**: ArduPlane SITL + MAVLink protokolü
- **Güvenlik Sistemi**: HSS (Hava Savunma Sistemi) bölgelerinde otomatik veto
- **Akıllı Rota Planlama**: A* algoritması ile HSS'den kaçınmalı güvenli rota
- **Canlı Harita**: Offline harita desteği (Leaflet + MBTiles)
- **Doğal Dil Komutları**: "T1 hedefine saldır" gibi komutlar

## 📁 Yapı

```
ares_v2/
├── main.py              # PyQt5 ana uygulama
├── run_ares.bat         # Tek tıkla başlatma
├── requirements.txt     # Python bağımlılıkları
├── agents/              # AI agent'ler
│   ├── orchestrator.py      # Ana koordinatör
│   ├── gemini_brain.py      # Gemini AI komutan
│   ├── worker_tools.py      # A* rota planlama
│   └── safety_guard.py      # Güvenlik doğrulayıcı
├── sim/                 # Simülasyon backend
│   ├── server.py            # Flask REST API
│   └── mavlink_simple.py    # MAVLink iletişim
├── ui/                  # Web arayüzü
│   ├── window.py            # PyQt pencere wrapper
│   ├── map_main.html        # Harita UI
│   └── map_bridge.py        # Python-JS köprüsü
└── assets/              # Harita karoları
    └── gokce_ada.mbtiles
```

## 🚀 Hızlı Başlangıç

### 1. Gereksinimler
```bash
pip install -r requirements.txt
```

### 2. API Key Ayarla
`.env` dosyası oluştur ve Gemini API key'ini ekle:
```env
GOOGLE_API_KEY=your-api-key-here
```
> API key almak için: https://aistudio.google.com/app/apikey

### 3. SITL'i Başlat
```bash
# Terminal 1: ArduPlane SITL (Fixed Wing)
sim_vehicle.py -v ArduPlane --console --map
```

### 4. Sistemi Başlat
```bash
# Terminal 2: ARES'i başlat
run_ares.bat
```

## 🎮 Kullanım

Arayüzde komut verin:
- **"T1 hedefine saldır"** → Rota planlar, güvenli ise uçağı gönderir
- **"T3'ü vur"** → HSS içinde olduğu için VETO edilir
- **"Radar jeneratörüne git"** → En yakın hedefi bulur ve rota çizer

## 🛡️ Güvenlik Özellikleri

Safety Validator kontrolleri:
- ✅ Batarya seviyesi (min %20)
- ✅ Maksimum menzil (15 km)
- ✅ **HSS bölgesi kontrolü** (hedef yasak bölgede mi?)
- ✅ Rota HSS'den geçiyor mu? (A* ile kaçınma)

## 🧠 Agent Akışı

```
Kullanıcı Komutu
    ↓
[COMMANDER] Gemini AI → Hedef seçimi + gerekçe
    ↓
[WORKER] A* → HSS'den kaçınmalı rota hesaplama
    ↓
[SAFETY] Validator → Güvenlik analizi
    ↓ (ONAY)
[DOER] → MAVLink ile uçağa mission upload
    ↓
AUTO modda rota takibi
```

## 📡 API Endpoints

- `GET /telemetry` - Uçak telemetrisi
- `GET /targets` - Kara hedefleri
- `GET /no_fly_zones` - HSS bölgeleri
- `POST /action/upload_mission` - Rota yükleme

## 🔧 Yapılandırma

**Gemini API Key**: `.env` dosyasında:
```env
GOOGLE_API_KEY=your-actual-key
```

**SITL Bağlantısı**: `sim/mavlink_simple.py`:
```python
connection_string='tcp:127.0.0.1:5762'
```

**Not**: `.env.example` dosyasını `.env` olarak kopyalayıp API key'inizi ekleyin.

## 📝 Notlar

- Fixed-wing uçak için **AUTO mod + mission protokolü** kullanılır
- Rota temizleme: `mission_clear_all` → `mission_count` → `mission_item` → AUTO
- HSS bölgeleri: SAM ve AAA sistemleri (150-350m yarıçaplı)
- Test senaryosu: T3 hedefi SAM-1 içinde (veto testi)

## 🏗️ Geliştirme

**Yeni hedef ekleme**: `sim/server.py` → `ground_targets` listesi

**HSS bölgesi ekleme**: `sim/server.py` → `no_fly_zones` listesi

**Agent davranışı**: `agents/` klasöründeki ilgili dosyayı düzenle

---

**Proje Durumu**: ✅ Operasyonel - Mission upload ve HSS veto sistemi çalışıyor
