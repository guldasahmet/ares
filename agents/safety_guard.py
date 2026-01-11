import math

class SafetyValidator:
    def __init__(self):
        self.MIN_BATTERY = 20
        self.MAX_RANGE_KM = 15.0
    
    def _distance_to_point(self, lat1, lon1, lat2, lon2):
        """İki nokta arasındaki mesafe (km)"""
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
        
    def validate_mission(self, route_data, uav_status, hss_zones=None, target_coord=None):
        """
        Görev güvenlik kontrolü
        - Batarya kontrolü
        - Menzil kontrolü
        - HEDEF HSS İÇİNDE Mİ kontrolü (YENİ!)
        """
        battery = uav_status.get('battery', 0)
        if battery < self.MIN_BATTERY:
            return False, f"VETO: Kritik Batarya (%{battery})."

        dist = route_data.get('distance_km', 0)
        if dist > self.MAX_RANGE_KM:
            return False, f"VETO: Hedef menzil dışında ({dist:.1f} km)."
        
        # YENİ: Hedefin kendisi HSS bölgesi içinde mi?
        if hss_zones and target_coord:
            target_lat = target_coord.get('lat')
            target_lon = target_coord.get('lon')
            
            for hss in hss_zones:
                hss_lat = hss.get('lat')
                hss_lon = hss.get('lon')
                hss_radius_km = hss.get('radius', 0) / 1000.0  # metreden km'ye
                
                distance = self._distance_to_point(target_lat, target_lon, hss_lat, hss_lon)
                
                if distance < hss_radius_km:
                    hss_id = hss.get('id', 'Bilinmeyen')
                    return False, f"🚫 VETO: Hedef {hss_id} HSS bölgesi içinde! Saldırı yasak."
        
        return True, "✅ GÜVENLİK ONAYI: Rota temiz."