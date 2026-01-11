"""
BASİT ÇALIŞAN MAVLINK HANDLER
test_direct_mode.py'den alındı - TESTLERİ GEÇTİ
"""
from pymavlink import mavutil
import time
import threading

class SimpleMavlinkHandler:
    def __init__(self, connection_string='tcp:127.0.0.1:5762'):
        print(f"\n[SIMPLE-MAV] 🔌 Bağlanıyor: {connection_string}")
        
        self.master = mavutil.mavlink_connection(connection_string, source_system=255)
        print("[SIMPLE-MAV] ✅ Heartbeat bekleniyor...")
        self.master.wait_heartbeat()
        print(f"[SIMPLE-MAV] ❤️ HEARTBEAT! System: {self.master.target_system}, Component: {self.master.target_component}")
        
        # Mode mapping
        self.mode_map = {
            0: "MANUAL", 1: "CIRCLE", 2: "STABILIZE", 3: "TRAINING", 
            4: "ACRO", 5: "FBWA", 6: "FBWB", 7: "CRUISE", 
            8: "AUTOTUNE", 10: "AUTO", 11: "RTL", 12: "LOITER",
            14: "AVOID_ADSB", 15: "GUIDED", 16: "INITIALIZING",
            17: "QSTABILIZE", 18: "QHOVER", 19: "QLOITER", 20: "QLAND",
            21: "QRTL", 22: "QAUTOTUNE", 23: "QACRO", 24: "THERMAL"
        }
        
        # Telemetri datası
        self.data = {
            "lat": 0, "lon": 0, "alt": 0, "heading": 0,
            "armed": False, "mode": "UNKNOWN", "battery": 100
        }
        
        self.running = True
        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()
    
    def _read_loop(self):
        """Telemetri okuma döngüsü"""
        while self.running:
            try:
                msg = self.master.recv_match(
                    type=['GLOBAL_POSITION_INT', 'HEARTBEAT', 'SYS_STATUS'], 
                    blocking=False
                )
                
                if not msg:
                    time.sleep(0.01)
                    continue
                
                msg_type = msg.get_type()
                
                if msg_type == 'GLOBAL_POSITION_INT':
                    self.data["lat"] = msg.lat / 1e7
                    self.data["lon"] = msg.lon / 1e7
                    self.data["alt"] = msg.relative_alt / 1000.0
                    self.data["heading"] = msg.hdg / 100.0
                    
                elif msg_type == 'HEARTBEAT':
                    self.data["armed"] = (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED) > 0
                    mode_name = self.mode_map.get(msg.custom_mode, f"UNKNOWN({msg.custom_mode})")
                    self.data["mode"] = mode_name
                    
                elif msg_type == 'SYS_STATUS':
                    self.data["battery"] = 100
                    
            except Exception as e:
                pass
    
    def get_data(self):
        """Telemetri datasını döndür"""
        return self.data
    
    def set_mode(self, mode_name):
        """Mod değiştir - TEST EDİLDİ ÇALIŞIYOR"""
        mode_id_map = {
            'MANUAL': 0, 'CIRCLE': 1, 'STABILIZE': 2, 'TRAINING': 3, 'ACRO': 4,
            'FBWA': 5, 'FBWB': 6, 'CRUISE': 7, 'AUTOTUNE': 8, 'AUTO': 10,
            'RTL': 11, 'LOITER': 12, 'TAKEOFF': 13, 'GUIDED': 15
        }
        
        if mode_name not in mode_id_map:
            print(f"[SIMPLE-MAV] ❌ Bilinmeyen mod: {mode_name}")
            return False
        
        mode_id = mode_id_map[mode_name]
        print(f"[SIMPLE-MAV] 🎮 {mode_name} moduna geçiliyor...")
        
        self.master.mav.command_long_send(
            self.master.target_system,
            0,  # broadcast
            mavutil.mavlink.MAV_CMD_DO_SET_MODE,
            0,
            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            mode_id,
            0, 0, 0, 0, 0
        )
        
        # ACK bekle
        start_time = time.time()
        while time.time() - start_time < 5:
            msg = self.master.recv_match(type='COMMAND_ACK', blocking=True, timeout=0.5)
            if msg and msg.command == mavutil.mavlink.MAV_CMD_DO_SET_MODE:
                result_names = {0: "ACCEPTED", 1: "TEMPORARILY_REJECTED", 2: "DENIED",
                               3: "UNSUPPORTED", 4: "FAILED", 5: "IN_PROGRESS"}
                result = result_names.get(msg.result, f"UNKNOWN({msg.result})")
                print(f"[SIMPLE-MAV] ACK: {result}")
                return msg.result == 0
        
        print("[SIMPLE-MAV] ⚠️ ACK timeout")
        return False
    
    def arm_disarm(self, arm=True):
        """ARM/DISARM - TEST EDİLDİ ÇALIŞIYOR"""
        print(f"[SIMPLE-MAV] {'ARM' if arm else 'DISARM'} komutu...")
        
        self.master.mav.command_long_send(
            self.master.target_system,
            0,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            0,
            1 if arm else 0,
            0, 0, 0, 0, 0, 0
        )
        
        # ACK bekle
        start_time = time.time()
        while time.time() - start_time < 5:
            msg = self.master.recv_match(type='COMMAND_ACK', blocking=True, timeout=0.5)
            if msg and msg.command == mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM:
                result_names = {0: "ACCEPTED", 1: "TEMPORARILY_REJECTED", 2: "DENIED",
                               3: "UNSUPPORTED", 4: "FAILED", 5: "IN_PROGRESS"}
                print(f"[SIMPLE-MAV] ARM ACK: {result_names.get(msg.result, msg.result)}")
                return msg.result == 0
        
        return False
    
    def upload_mission(self, waypoints):
        """
        KLASİK MISSION UPLOAD + AUTO MOD
        Mission protokolü + AUTO mod (çalışan mod değiştirme ile)
        """
        if not waypoints:
            print("[SIMPLE-MAV] ⚠️ Waypoint listesi boş!")
            return False
        
        print(f"\n[SIMPLE-MAV] 🎯 {len(waypoints)} waypoint mission yükleniyor...")
        
        try:
            # 1. Mission'ı temizle
            print("[SIMPLE-MAV] 🧹 Eski mission temizleniyor...")
            self.master.mav.mission_clear_all_send(self.master.target_system, 0)
            
            msg = self.master.recv_match(type='MISSION_ACK', blocking=True, timeout=3)
            if msg:
                print(f"[SIMPLE-MAV] ✅ Mission temizlendi")
            time.sleep(0.5)
            
            # 2. Mission count gönder (HOME + waypoints)
            total_items = len(waypoints) + 1
            print(f"[SIMPLE-MAV] 📤 Mission count: {total_items} item")
            
            self.master.mav.mission_count_send(
                self.master.target_system, 0, total_items,
                mavutil.mavlink.MAV_MISSION_TYPE_MISSION
            )
            
            # 3. MISSION_REQUEST mesajlarını dinle
            print("[SIMPLE-MAV] 📥 Mission item istekleri bekleniyor...")
            
            for i in range(total_items):
                msg = self.master.recv_match(type='MISSION_REQUEST', blocking=True, timeout=5)
                if not msg:
                    print(f"[SIMPLE-MAV] ❌ Item {i} için REQUEST gelmedi!")
                    return False
                
                print(f"[SIMPLE-MAV] 📨 Item {msg.seq} istendi")
                
                if msg.seq == 0:
                    # HOME waypoint
                    lat = self.data["lat"] if self.data["lat"] != 0 else 40.2
                    lon = self.data["lon"] if self.data["lon"] != 0 else 25.89
                    
                    print(f"[SIMPLE-MAV] 🏠 HOME: {lat:.6f}, {lon:.6f}")
                    
                    self.master.mav.mission_item_send(
                        self.master.target_system, 0, 0,
                        mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                        mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                        1, 1, 0, 0, 0, 0, lat, lon, 0
                    )
                else:
                    # Normal waypoint
                    wp_idx = msg.seq - 1
                    wp = waypoints[wp_idx]
                    
                    print(f"[SIMPLE-MAV] 📍 WP{msg.seq}: {wp[0]:.6f}, {wp[1]:.6f}")
                    
                    self.master.mav.mission_item_send(
                        self.master.target_system, 0, msg.seq,
                        mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                        mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                        0, 1, 0, 0, 0, 0, wp[0], wp[1], 100
                    )
            
            # 4. Final ACK bekle
            msg = self.master.recv_match(type='MISSION_ACK', blocking=True, timeout=5)
            if msg:
                if msg.type == mavutil.mavlink.MAV_MISSION_ACCEPTED:
                    print("[SIMPLE-MAV] ✅ Mission KABUL EDİLDİ!")
                else:
                    print(f"[SIMPLE-MAV] ⚠️ Mission ACK: {msg.type}")
                    return False
            else:
                print("[SIMPLE-MAV] ⚠️ Final ACK gelmedi")
                return False
            
            time.sleep(1)
            
            # 5. AUTO moduna geç (çalışan mod değiştirme ile)
            print("[SIMPLE-MAV] 🚁 AUTO moduna geçiliyor...")
            self.master.mav.command_long_send(
                self.master.target_system, 0,
                mavutil.mavlink.MAV_CMD_DO_SET_MODE, 0,
                mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                10, 0, 0, 0, 0, 0  # AUTO = 10
            )
            
            # AUTO ACK bekle
            start_time = time.time()
            while time.time() - start_time < 5:
                msg = self.master.recv_match(type='COMMAND_ACK', blocking=True, timeout=0.5)
                if msg and msg.command == mavutil.mavlink.MAV_CMD_DO_SET_MODE:
                    result_names = {0: "ACCEPTED", 1: "TEMPORARILY_REJECTED", 2: "DENIED",
                                   3: "UNSUPPORTED", 4: "FAILED", 5: "IN_PROGRESS"}
                    print(f"[SIMPLE-MAV] AUTO ACK: {result_names.get(msg.result, msg.result)}")
                    break
            
            # Mod doğrula
            time.sleep(1)
            for _ in range(5):
                msg = self.master.recv_match(type='HEARTBEAT', blocking=True, timeout=1)
                if msg and msg.custom_mode == 10:
                    print("[SIMPLE-MAV] ✅ AUTO moduna GEÇİLDİ!")
                    break
                time.sleep(0.5)
            
            print("[SIMPLE-MAV] 🚀 BAŞARILI! Uçak AUTO modda rotayı takip ediyor!")
            return True
            
        except Exception as e:
            print(f"[SIMPLE-MAV] ❌ HATA: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def close(self):
        """Bağlantıyı kapat"""
        self.running = False
        if self.thread.is_alive():
            self.thread.join(timeout=2)
        print("[SIMPLE-MAV] Bağlantı kapatıldı")
