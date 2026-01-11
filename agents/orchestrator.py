import requests
import json
import time
from agents.gemini_brain import MissionCommander
from agents.worker_tools import WorkerTools
from agents.safety_guard import SafetyValidator

class AgentOrchestrator:
    def __init__(self, log_callback):
        self.log_callback = log_callback
        self.commander = MissionCommander()
        self.worker = WorkerTools()
        self.validator = SafetyValidator()
        self.world_data = {"uav": {}, "enemies": [], "targets": [], "hss": []}

    def update_world_data(self):
        try:
            base_url = "http://localhost:5000"
            self.world_data["uav"] = requests.get(f"{base_url}/telemetry", timeout=0.1).json()
            self.world_data["enemies"] = requests.get(f"{base_url}/enemies", timeout=0.1).json()
            self.world_data["targets"] = requests.get(f"{base_url}/targets", timeout=0.1).json()
            self.world_data["hss"] = requests.get(f"{base_url}/no_fly_zones", timeout=0.1).json()
        except: pass
        return self.world_data

    def execute_pipeline(self, user_text):
        # 1. Veri Topla
        self.update_world_data() 
        self.log_callback(f"🔵 [USER]: \"{user_text}\"", "USER")
        self.log_callback("⏳ [SYSTEM]: Ajanlar göreve çağrılıyor...", "SYSTEM")
        time.sleep(0.1)

        # 2. COMMANDER
        plan = self.commander.analyze_intent(user_text, self.world_data)
        if "error" in plan:
            self.log_callback(f"🔴 [ERROR]: {plan.get('error')}", "ERROR")
            return None
        
        target_id = plan.get('target_id', 'Bilinmiyor')
        reasoning = plan.get('reasoning', '...')
        self.log_callback(f"🧠 [COMMANDER]: Hedef {target_id} seçildi.\n   └─ Gerekçe: {reasoning}", "INFO")

        # 3. WORKER
        start_pos = (self.world_data["uav"].get("lat", 0), self.world_data["uav"].get("lon", 0))
        target_coord = plan.get('target_coordinate')
        if not target_coord: return None
        target_pos = (target_coord['lat'], target_coord['lon'])
        
        self.log_callback(f"🛠️ [WORKER]: A* Algoritması çalıştırılıyor...", "SYSTEM")
        route_data = self.worker.calculate_astar_path(start_pos, target_pos, self.world_data["hss"])
        dist = route_data.get('distance_km', 0)
        self.log_callback(f"📏 [WORKER]: Rota bulundu ({len(route_data['route'])} WP, {dist:.2f} km).", "INFO")

        # 4. SAFETY (HSS VE HEDEF KOORDİNATI İLE)
        self.log_callback(f"🛡️ [SAFETY]: Risk analizi yapılıyor...", "SYSTEM")
        is_safe, msg = self.validator.validate_mission(
            route_data, 
            self.world_data["uav"],
            hss_zones=self.world_data["hss"],
            target_coord=target_coord
        )
        
        if is_safe:
            self.log_callback(f"🟢 [SAFETY]: ONAY VERİLDİ. ({msg})", "SUCCESS")
            
            # 5. DOER
            try:
                base_url = "http://localhost:5000"
                self.log_callback(f"✈️ [DOER]: Görev paketi otopilota gönderiliyor...", "SYSTEM")
                
                # ROTAYI TEMİZLE VE GÖNDER
                # UI ve MAVLink için saf liste formatına çeviriyoruz: [[lat, lon], [lat, lon]]
                clean_route = []
                for point in route_data['route']:
                    if isinstance(point, (list, tuple)):
                        clean_route.append([float(point[0]), float(point[1])])
                    elif isinstance(point, dict):
                        clean_route.append([float(point['lat']), float(point['lon'])])

                # MAVLink'e gönder
                requests.post(f"{base_url}/action/upload_mission", json={"route": clean_route})
                self.log_callback("✅ [DOER]: Rota yüklendi. Görev başlatıldı.", "SUCCESS")
                
                return clean_route # UI'ya bu temiz listeyi döndür
                    
            except Exception as e:
                self.log_callback(f"⚠️ [DOER]: Bağlantı Hatası: {e}", "ERROR")
                return None
        else:
            self.log_callback(f"❌ [SAFETY]: VETO! ({msg})", "ERROR")
            return None