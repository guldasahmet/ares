import sys
import os
import threading

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, pyqtSlot, QObject, pyqtSignal
from PyQt5.QtWebChannel import QWebChannel

# Ajan Orkestratörünü import et
from agents.orchestrator import AgentOrchestrator

class BackendBridge(QObject):
    # Logları UI'ya göndermek için sinyal
    log_signal = pyqtSignal(str, str)
    # Haritadaki markerları güncellemek için sinyal
    marker_signal = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.agent_orchestrator = AgentOrchestrator(
            log_callback=lambda msg, type: self.log_signal.emit(msg, type)
        )

    @pyqtSlot(str)
    def receiveData(self, text):
        """UI'dan gelen mesajı alır ve Thread içinde işler"""
        t = threading.Thread(target=self.process_in_background, args=(text,))
        t.daemon = True 
        t.start()

    def process_in_background(self, text):
        route = self.agent_orchestrator.execute_pipeline(text)
        if route:
            self.marker_signal.emit(route)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ARES - Multi-Agent Tactical System")
        self.setGeometry(100, 100, 1280, 720)
        
        # Arka planı siyah yap (Yüklenirken beyaz parlamasın)
        self.setStyleSheet("background-color: #0a0e14;")

        # Web Engine
        self.browser = QWebEngineView()
        # Tarayıcı arka planını da siyah yap
        self.browser.setStyleSheet("background-color: #0a0e14;")
        
        # Backend Bridge
        self.bridge = BackendBridge()
        self.bridge.log_signal.connect(self.append_log) 
        self.bridge.marker_signal.connect(self.update_route_on_map)

        # Web Channel
        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.bridge)
        self.browser.page().setWebChannel(self.channel)

        # HTML Yükle
        file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "ui", "map_main.html"))
        self.browser.setUrl(QUrl.fromLocalFile(file_path))

        # --- KENAR BOŞLUKLARINI SIFIRLAMA (FIX) ---
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0) # Sol, Üst, Sağ, Alt boşlukları 0 yap
        layout.setSpacing(0)                  # Elemanlar arası boşluğu 0 yap
        layout.addWidget(self.browser)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def append_log(self, message, type="INFO"):
        """JS fonksiyonunu çağırarak log ekler"""
        # Tırnak işaretlerini kaçış karakteriyle düzelt
        safe_msg = message.replace("'", "\\'")
        js_code = f"if(window.appendLog) window.appendLog('{safe_msg}', '{type}');"
        self.browser.page().runJavaScript(js_code)

    def update_route_on_map(self, route):
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())