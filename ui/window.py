import os
import sys
import time
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QUrl, QThread, pyqtSignal, Qt
from ui.map_bridge import MapBridge
from agents.orchestrator import AgentOrchestrator

# --- THREAD SINIFI (Veri Akışı) ---
class DataWorker(QThread):
    data_updated = pyqtSignal(dict)

    def __init__(self, orchestrator):
        super().__init__()
        self.orchestrator = orchestrator
        self.running = True

    def run(self):
        while self.running:
            try:
                data = self.orchestrator.update_world_data()
                self.data_updated.emit(data)
            except Exception as e:
                print(f"Data Thread Hatası: {e}")
            time.sleep(0.5)

    def stop(self):
        self.running = False
        self.wait()

# --- ANA PENCERE ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ARES - Multi-Agent Tactical System")
        
        # DÜZELTME 1: Poyraz projesindeki gibi Tam Ekran başlatıyoruz
        self.setWindowState(Qt.WindowMaximized)
        self.setStyleSheet("background-color: #121212; color: white;")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0) # Kenar boşluklarını sıfırla
        layout.setSpacing(0)

        # 1. SOL PANEL: Harita
        self.web_view = QWebEngineView()
        self.map_bridge = MapBridge(self)
        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.map_bridge)
        self.web_view.page().setWebChannel(self.channel)
        
        map_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "map_main.html"))
        self.web_view.setUrl(QUrl.fromLocalFile(map_path))
        
        # DÜZELTME 2: Poyraz oranları (Harita 4 birim yer kaplasın)
        layout.addWidget(self.web_view, 4)

        # 2. SAĞ PANEL: Loglar ve Kontrol
        right_panel = QWidget()
        # Panelin biraz belirgin olması için sınır çizgisi
        right_panel.setStyleSheet("border-left: 2px solid #333; background-color: #0f141a;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("background: #000; font-family: Consolas; font-size: 12px; border: 1px solid #333;")
        right_layout.addWidget(QLabel("📢 AGENT LOGS"))
        right_layout.addWidget(self.log_text)

        self.cmd_input = QLineEdit()
        self.cmd_input.setStyleSheet("background: #222; padding: 8px; border: 1px solid #555; color: white;")
        self.cmd_input.setPlaceholderText("Emir verin...")
        self.cmd_input.returnPressed.connect(self.run_command)
        right_layout.addWidget(self.cmd_input)
        
        btn = QPushButton("GÖNDER")
        btn.setStyleSheet("background: #00aa00; font-weight: bold; padding: 10px; border-radius: 5px;")
        btn.clicked.connect(self.run_command)
        right_layout.addWidget(btn)
        
        # DÜZELTME 3: Poyraz oranları (Sağ panel 1 birim yer kaplasın -> 4:1 Oranı)
        layout.addWidget(right_panel, 1)

        # --- SİSTEM BAŞLATMA ---
        self.orchestrator = AgentOrchestrator(self.add_log)
        self.current_route = []

        self.worker = DataWorker(self.orchestrator)
        self.worker.data_updated.connect(self.update_gui_slot)
        self.worker.start()

    def add_log(self, msg, type="INFO"):
        color = "lime" if type=="SUCCESS" else "red" if type=="ERROR" else "cyan" if type=="USER" else "white"
        self.log_text.append(f"<span style='color:{color}'>[{type}] {msg}</span>")
        sb = self.log_text.verticalScrollBar()
        sb.setValue(sb.maximum())

    def run_command(self):
        cmd = self.cmd_input.text()
        if not cmd: return
        self.cmd_input.clear()
        route = self.orchestrator.execute_pipeline(cmd)
        if route:
            self.current_route = [{"lat": p[0], "lon": p[1]} for p in route]

    def update_gui_slot(self, data):
        self.map_bridge.update_position(
            data["uav"].get("lat", 0),
            data["uav"].get("lon", 0),
            data["enemies"],
            data["targets"],
            data["hss"],
            data["uav"].get("heading", 0),
            self.current_route,
            True
        )

    def closeEvent(self, event):
        self.worker.stop()
        event.accept()