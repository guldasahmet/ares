import math

class WorkerTools:
    def calculate_astar_path(self, start_pos, target_pos, no_fly_zones):
        """Basit A* Simülasyonu"""
        path = []
        path.append(start_pos)
        
        mid_lat = (start_pos[0] + target_pos[0]) / 2
        mid_lon = (start_pos[1] + target_pos[1]) / 2
        
        collision = False
        for zone in no_fly_zones:
            dist = math.sqrt((mid_lat - zone['lat'])**2 + (mid_lon - zone['lon'])**2)
            if dist < 0.005: 
                collision = True
                break
        
        if collision:
            safe_waypoint = (mid_lat + 0.008, mid_lon - 0.008)
            path.append(safe_waypoint)
        
        path.append(target_pos)
        
        return {
            "route": path,
            "distance_km": self._calc_dist(start_pos, target_pos)
        }

    def check_threats(self, my_pos, enemies):
        threats = []
        for enemy in enemies:
            dist = self._calc_dist(my_pos, (enemy['lat'], enemy['lon']))
            if dist < 2.0:
                threats.append(enemy)
        return threats

    def _calc_dist(self, p1, p2):
        dy = (p1[0] - p2[0]) * 111
        dx = (p1[1] - p2[1]) * 111 * math.cos(math.radians(p1[0]))
        return math.sqrt(dx*dx + dy*dy)