from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
import json

class MapBridge(QObject):
    updateMapDataSignal = pyqtSignal(str) 
    mapClicked = pyqtSignal(float, float)
    
    def __init__(self, parent=None):
        super(MapBridge, self).__init__(parent)

    @pyqtSlot(float, float, list, list, list, float, list, bool)
    def update_position(self, lat, lon, enemies, targets, hss_regions, rotation, rota_list, hss_activate):
        """
        GUI Thread'inden gelen veriyi JS'ye aktarır.
        """
        # Verileri güvenli JSON formatına çevir
        # Not: JS tarafında parse edilecek
        try:
            if hasattr(self.parent(), 'web_view'):
                page = self.parent().web_view.page()
                
                # Listeleri JSON string'e çevir (Manuel string formatlama yerine json.dumps daha güvenlidir)
                enemy_json = json.dumps(enemies)
                target_json = json.dumps(targets)
                hss_json = json.dumps(hss_regions)
                route_json = json.dumps(rota_list)
                
                # JS Kodunu oluştur
                js_code = f"if (typeof window.updateMarkers === 'function') {{ " \
                          f"window.updateMarkers({lat}, {lon}, {enemy_json}, {target_json}, {hss_json}, " \
                          f"{rotation}, {route_json}, {str(hss_activate).lower()}); }}"
                
                page.runJavaScript(js_code)
        except Exception as e:
            print(f"Köprü Hatası: {e}")

    @pyqtSlot(str)
    def receiveData(self, data):
        try:
            parts = data.split()
            if len(parts) >= 2:
                print(f"📍 Harita Tıklandı: {parts[0]}, {parts[1]}")
        except:
            pass