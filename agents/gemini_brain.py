import google.generativeai as genai
import json
import os
import time
from dotenv import load_dotenv

# .env dosyasından API key'i yükle
load_dotenv()

class MissionCommander:
    def __init__(self):
        # API key'i .env dosyasından al
        self.api_key = os.getenv('GOOGLE_API_KEY')
        
        self.active = False
        if self.api_key and self.api_key != "your-api-key-here":
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-flash-latest')
                self.active = True
                print("✅ [BRAIN] Gemini Flash (Latest) Aktif!")
            except Exception as e:
                print(f"⚠️ [BRAIN] Bağlantı Hatası: {e}")
        else:
            print("⚠️ [BRAIN] API Key eksik! .env dosyasını kontrol edin.")

    def analyze_intent(self, user_text, world_data):
        """
        Kullanıcı emrini analiz eder. Hata alırsa bekleyip tekrar dener (Retry Logic).
        """
        if not self.active:
            return self._dummy_response()

        # --- AI PROMPT ---
        targets_list = world_data.get('targets', [])
        formatted_targets = []
        for i, t in enumerate(targets_list):
            formatted_targets.append(f"HEDEF {i+1} (ID: {t['id']}): {t['type']} -> {t['lat']},{t['lon']}")
            
        hss_info = json.dumps(world_data.get('hss', []), indent=2)
        uav_status = json.dumps(world_data.get('uav', {}), indent=2)

        prompt = f"""
        Sen ARES İHA Sisteminin Taktik Komutanısın.
        
        [DURUM]
        - İHA: {uav_status}
        - HSS Bölgeleri: {hss_info}
        
        [HEDEFLER (Harita Numaraları)]
        {json.dumps(formatted_targets, indent=2)}
        
        [EMİR]
        "{user_text}"
        
        [GÖREV]
        Operatörün emrine (örn: "Hedef 8'i vur") uygun hedefi seç.
        Sadece JSON formatında yanıt ver.
        
        {{
            "intent": "ATTACK" veya "RECON",
            "target_id": "Hedef ID",
            "target_coordinate": {{ "lat": 0.0, "lon": 0.0 }},
            "reasoning": "Sebep"
        }}
        """
        
        # --- TEKRAR DENEME MEKANİZMASI (RETRY LOOP) ---
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                clean_json = response.text.replace("```json", "").replace("```", "").strip()
                return json.loads(clean_json)
                
            except Exception as e:
                error_msg = str(e)
                # 429 = Hız Sınırı (Rate Limit), 500 = Sunucu Hatası
                if "429" in error_msg or "Quota" in error_msg or "500" in error_msg:
                    wait_time = (attempt + 1) * 2 # 2sn, 4sn, 6sn bekle
                    print(f"⚠️ [BRAIN] API Yoğun ({error_msg[:50]}...), {wait_time}sn bekleniyor...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"🔴 [BRAIN] Kritik Hata: {e}")
                    # Hata olsa bile sistemi kilitlememek için varsayılan bir hedef dönüyoruz
                    return {"error": str(e), "target_coordinate": {"lat": 40.205, "lon": 25.880}}
        
        return {"error": "API Yanıt Vermedi", "target_coordinate": {"lat": 40.205, "lon": 25.880}}

    def _dummy_response(self):
        return {
            "intent": "ATTACK",
            "target_coordinate": {"lat": 40.205, "lon": 25.880},
            "target_id": "UNKNOWN",
            "reasoning": "Simülasyon Modu (API Bağlantısı Yok)."
        }