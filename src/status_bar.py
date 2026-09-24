from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer
import psutil
import platform
import subprocess

class StatusBar(QWidget):
    def __init__(self, config, parent=None):
        super().__init__(parent)

        self.config = config
        
        self.setFixedHeight(30)
        self.setObjectName("status_bar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(6)

        self.status_indicator = QLabel("●")
        self.status_indicator.setObjectName("status_indicator")
        self.status_indicator.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.status_label = QLabel("NVR conectado")
        self.status_label.setObjectName("status_label")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.resource_label = QLabel("CPU: --    RAM: --")
        self.resource_label.setObjectName("resource_label")
        self.resource_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        self.process = psutil.Process()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_resources)
        self.timer.start(2000)
        self.update_resources()

        layout.addWidget(self.status_indicator)
        layout.addWidget(self.status_label)

        layout.addStretch()

        layout.addWidget(self.resource_label)

    def update_resources(self):
        #Visualizacion de utilizacion de recursos por la APP
        cpu = self.process.cpu_percent()
        ram = self.process.memory_info().rss
        ram_mb = ram / (1024 * 1024)

        self.resource_label.setText(f"CPU: {cpu:.0f} %    RAM: {ram_mb:.0f} MB")

        #Test de conectividad hacia el NVR
        if self.check_nvr_ping():
            self.status_indicator.setStyleSheet("color: #3FB950;")
            self.status_label.setText("NVR conectado")
        else:
            self.status_indicator.setStyleSheet("color: #F85149;")
            self.status_label.setText("NVR no disponible")

    def check_nvr_ping(self):
        nvr_ip = self.config.get("NVR_IP")

        if not nvr_ip:
            return False

        if platform.system() == "Windows":
            command = ["ping", "-n", "1", "-w", "1000", nvr_ip]
        else:
            command = ["ping", "-c", "1", "-W", "1", nvr_ip]

        result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        return result.returncode == 0
