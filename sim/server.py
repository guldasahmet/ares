import sys
import os
import logging

# 1. Proje ana dizinini Python yoluna ekle
current_dir = os.path.dirname(os.path.abspath(__file__)) 
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Assets klasörünün yolu
ASSETS_DIR = os.path.join(parent_dir, 'assets')

from flask import Flask, jsonify, send_from_directory, request
# --- YENİ EKLENTİ ---
try:
    from flask_cors import CORS
except ImportError:
    print("Lütfen 'pip install flask-cors' komutunu çalıştırın!")
    sys.exit(1)

import threading
import time
import math

# Flask loglarını kapat
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Import güvenliği - YENİ BASİT HANDLER KULLAN
try:
    from sim.mavlink_simple import SimpleMavlinkHandler
except ImportError:
    from mavlink_simple import SimpleMavlinkHandler

app = Flask(__name__)

# --- CORS AYARI (HAYAT KURTARAN SATIR) ---
# Bu satır, file:// protokolünden gelen isteklere izin verir.
CORS(app) 

# MAVLink Bağlantısı - TEST EDİLMİŞ ÇALIŞAN HANDLER
print("\n" + "="*60)
print("🚀 BASİT MAVLINK HANDLER KULLANILIYOR (TEST EDİLDİ)")
print("="*60 + "\n")
mav_handler = SimpleMavlinkHandler(connection_string='tcp:127.0.0.1:5762')

# --- SENARYO VERİLERİ ---

# 1. KARA HEDEFLERİ
ground_targets = [
    {"id": "T1", "type": "SIGINAK_ANA", "lat": 40.20600, "lon": 25.89400},
    {"id": "T2", "type": "RADAR_JENERATOR", "lat": 40.21600, "lon": 25.88900},
    {"id": "T3", "type": "CEPHANELIK_A", "lat": 40.21000, "lon": 25.89400},  # SAM-1 HSS içinde (TEST)
    {"id": "T4", "type": "IKMAL_NOKTASI", "lat": 40.20700, "lon": 25.91000},
    {"id": "T5", "type": "SIGINAK_YEDEK", "lat": 40.21000, "lon": 25.88000},
    {"id": "T6", "type": "MOBIL_BATARYA", "lat": 40.20500, "lon": 25.87700},
    {"id": "T7", "type": "PIST_BASI_DEPO", "lat": 40.20100, "lon": 25.88800},
    {"id": "T8", "type": "GOZLEM_KULESI", "lat": 40.20300, "lon": 25.89100}
]

# 2. HSS BÖLGELERİ
no_fly_zones = [
    {"id": "SAM-1", "lat": 40.20999, "lon": 25.89399, "radius": 350},  # T3 buraya koyuldu
    {"id": "SAM-1B", "lat": 40.21350, "lon": 25.88900, "radius": 200},
    {"id": "AAA-1", "lat": 40.20457, "lon": 25.90301, "radius": 250},
    {"id": "AAA-1B", "lat": 40.20700, "lon": 25.90750, "radius": 180},
    {"id": "SAM-2", "lat": 40.21000, "lon": 25.88335, "radius": 150},
    {"id": "SAM-2B", "lat": 40.20700, "lon": 25.87900, "radius": 150}
]

# 3. DÜŞMAN İHA'LAR
enemies = [
    {
        "id": "E1", "type": "PATROL",
        "center_lat": 40.210, "center_lon": 25.885, 
        "radius": 0.004, "angle": 0, "speed": 0.02,   
        "lat": 0, "lon": 0, "heading": 0 
    },
    {
        "id": "E2", "type": "INTERCEPTOR",
        "center_lat": 40.200, "center_lon": 25.895, 
        "radius": 0.003, "angle": 180, "speed": 0.03,   
        "lat": 0, "lon": 0, "heading": 0
    }
]

# FİZİK MOTORU
def physics_loop():
    while True:
        for enemy in enemies:
            enemy["angle"] += enemy["speed"]
            offset_lat = enemy["radius"] * math.cos(enemy["angle"])
            offset_lon = (enemy["radius"] / 0.76) * math.sin(enemy["angle"])
            enemy["lat"] = enemy["center_lat"] + offset_lat
            enemy["lon"] = enemy["center_lon"] + offset_lon
            heading_rad = math.atan2(offset_lon, offset_lat)
            enemy["heading"] = (math.degrees(heading_rad) + 180) % 360
        time.sleep(0.05)

threading.Thread(target=physics_loop, daemon=True).start()

# --- API ENDPOINTLERİ ---

@app.route('/telemetry')
def get_telemetry(): return jsonify(mav_handler.get_data())

@app.route('/enemies')
def get_enemies(): return jsonify(enemies)

@app.route('/targets')
def get_targets(): return jsonify(ground_targets)

@app.route('/no_fly_zones')
def get_nfz(): return jsonify(no_fly_zones)

@app.route('/assets/<path:filename>')
def serve_assets(filename): return send_from_directory(ASSETS_DIR, filename)

# --- AKSİYON ENDPOINTLERİ ---

@app.route('/action/arm', methods=['POST'])
def action_arm():
    mav_handler.set_mode("GUIDED")
    time.sleep(0.5)
    mav_handler.arm_disarm(True)
    return jsonify({"status": "ARM sent"})

@app.route('/action/takeoff', methods=['POST'])
def action_takeoff():
    mav_handler.takeoff(50)
    return jsonify({"status": "TAKEOFF sent"})

# Kısa endpoint adı (UI test butonu için)
@app.route('/route', methods=['POST'])
def action_route():
    data = request.json
    route = data.get("route", [])
    if route:
        mav_handler.upload_mission(route)
        return jsonify({"status": "MISSION uploaded", "count": len(route)})
    return jsonify({"status": "NO ROUTE"}), 400

@app.route('/action/upload_mission', methods=['POST'])
def action_mission():
    data = request.json
    route = data.get("route", [])
    if route:
        mav_handler.upload_mission(route)
        return jsonify({"status": "MISSION uploaded", "count": len(route)})
    return jsonify({"status": "NO ROUTE"}), 400

if __name__ == '__main__':
    print(f"[SERVER] Savaş Simülasyonu Başlatıldı. Port: 5000")
    print(f"[SERVER] Harita Kaynağı: {ASSETS_DIR}")
    print(f"[SERVER] CORS Aktif: Arayüz bağlantısı güvenli.")
    app.run(host='0.0.0.0', port=5000, debug=False)