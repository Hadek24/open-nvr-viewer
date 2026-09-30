from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QComboBox, QLabel, QGraphicsDropShadowEffect
from src.video_thread import FFmpegThread
from src.video_frame import VideoFrame

class HoverAwareComboBox(QComboBox):
    def __init__(self, owner, parent=None):
        super().__init__(parent)
        self.owner = owner

    def showPopup(self):
        self.owner.popup_open = True
        super().showPopup()

    def hidePopup(self):
        super().hidePopup()
        self.owner.popup_open = False
        if not self.owner.rect().contains(
            self.owner.mapFromGlobal(self.owner.cursor().pos())):
            self.owner.controls_widget.hide()

class CameraWidget(QWidget):
    def __init__(self, slot_index, initial_channel, parent_grid, config):
        super().__init__()
        self.slot_index = slot_index
        self.current_channel = initial_channel
        self.parent_grid = parent_grid
        self.config = config
        self.ffmpeg_thread = None
        self.is_muted = True
        self.popup_open = False
        self.reconnect_attempts = 0
        self.connection_timer = QTimer(self)
        self.connection_timer.setSingleShot(True)
        self.connection_timer.timeout.connect(self.handle_connection_timeout)
        self.frame_timeout_timer = QTimer(self)
        self.frame_timeout_timer.setSingleShot(True)
        self.frame_timeout_timer.timeout.connect(self.handle_frame_timeout)
        # Temporizador para ocultar el estado Connected
        self.status_connected_timer = QTimer(self)
        self.status_connected_timer.setSingleShot(True)
        self.status_connected_timer.timeout.connect(self.hide_connected_status)
        self.reconnect_timer = QTimer(self)
        self.reconnect_timer.setSingleShot(True)
        self.reconnect_timer.timeout.connect(self.handle_auto_reconnect)
        self.init_ui()
        if self.current_channel != "Vacío":
            self.play_stream("2")

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.video_container = QWidget()
        self.video_frame = VideoFrame(self)
        self.status_label = QLabel("Desconectado", self.video_container)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_status("Desconectado", "red")
        video_layout = QGridLayout(self.video_container)
        video_layout.setContentsMargins(0, 0, 0, 0)
        video_layout.addWidget(self.video_frame, 0, 0)
        self.status_label.raise_()
        layout.addWidget(self.video_container)
        self.controls_widget = QWidget(self.video_container)
        self.controls_widget.setGeometry(0, 0, self.video_container.width(), 40)
        self.controls_widget.hide()
        controls_layout = QHBoxLayout(self.controls_widget)
        self.cam_selector = HoverAwareComboBox(self)
        self.cam_selector.addItem("Vacío")
        for ch in range(1, self.config["TOTAL_CHANNELS"] + 1):
            self.cam_selector.addItem(f"Cam {ch}", str(ch))
        if self.current_channel == "Vacío":
            self.cam_selector.setCurrentIndex(0)
        else:
            index = self.cam_selector.findData(self.current_channel)
            if index != -1:
                self.cam_selector.setCurrentIndex(index)
        self.cam_selector.currentIndexChanged.connect(self.handle_channel_changed)
        controls_layout.addWidget(self.cam_selector)
        self.audio_btn = QPushButton("🔇")
        self.audio_btn.setFixedWidth(40)
        self.audio_btn.setEnabled(False)
        self.audio_btn.setToolTip("Audio pendiente de implementación")
        controls_layout.addWidget(self.audio_btn)
        self.reconnect_btn = QPushButton("↻")
        self.reconnect_btn.setFixedWidth(40)
        self.reconnect_btn.setToolTip("Reconectar")
        self.reconnect_btn.clicked.connect(self.handle_reconnect)
        controls_layout.addWidget(self.reconnect_btn)
        controls_layout.addStretch()
        self.setLayout(layout)

    def set_status(self, text, color): #Permite centralizar la edicion grafica de los estados de las camaras
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 20px;")
        self.status_label.setText(text)
        self.status_label.show()
        if not self.status_label.graphicsEffect(): #Agrega sombra a los estados
            shadow = QGraphicsDropShadowEffect(self.status_label)
            shadow.setBlurRadius(20)
            shadow.setOffset(0, 0)
            shadow.setColor(Qt.GlobalColor.white)
            self.status_label.setGraphicsEffect(shadow)

    def play_stream(self, stream_type):
        if self.current_channel == "Vacío":
            return
        self.stop_stream()
        self.set_status("Conectando...", "orange")
        channel_code = f"{self.current_channel}0{stream_type}"
        url = f"rtsp://{self.config['NVR_USER']}:{self.config['NVR_PASS']}@{self.config['NVR_IP']}:{self.config['NVR_PORT']}/Streaming/channels/{channel_code}"
        if stream_type == "1":
            width, height = 2560, 1440
        else:
            width, height = 640, 360
        thread = FFmpegThread(url, width, height)
        thread.frame_ready.connect(lambda image, t=thread: self.handle_frame(image, t))
        thread.stream_ready.connect(self.handle_stream_ready)
        thread.stream_error.connect(self.handle_stream_error)
        self.ffmpeg_thread = thread
        thread.start()
        self.connection_timer.start(10000)

    def stop_stream(self):
        self.connection_timer.stop()
        self.frame_timeout_timer.stop()
        self.status_connected_timer.stop()
        self.reconnect_timer.stop()
        if self.ffmpeg_thread:
            self.ffmpeg_thread.stop()
            self.ffmpeg_thread.wait(1000)
            self.ffmpeg_thread = None
        self.video_frame.image = None
        self.video_frame.update()

    def handle_frame(self, image, thread):
        if thread is not self.ffmpeg_thread:
            return
        self.reconnect_timer.stop()
        """
        #Test frames
        if not hasattr(self, "_debug_frame_count"):
            self._debug_frame_count = 0

        self._debug_frame_count += 1

        if self._debug_frame_count % 30 == 0:
            print(f"CAM {self.slot_index}: {self._debug_frame_count} frames")
        #Test frames
        """
        self.reconnect_attempts = 0
        self.video_frame.set_image(image)
        if self.status_label.text() != "Conectado":
            self.set_status("Conectado", "#00FF00")
            self.status_connected_timer.start(5000)
        self.frame_timeout_timer.start(5000)

    def hide_connected_status(self):
        self.status_label.hide()

    def handle_connection_timeout(self):
        self.set_status("SIN SEÑAL", "red")
        if self.ffmpeg_thread:
            self.ffmpeg_thread.stop()
            self.ffmpeg_thread.wait(1000)
            self.ffmpeg_thread = None
        self.reconnect_attempts += 1
        if self.reconnect_attempts <= 6:
            self.reconnect_timer.start(10000)
        else:
            self.reconnect_timer.start(600000)

    def handle_frame_timeout(self):
        #print(">>> TIMEOUT <<<") #Prueba para timeout de camaras.
        self.set_status("SIN SEÑAL", "red")
        self.video_frame.image = None
        self.video_frame.update()
        self.reconnect_timer.start(10000)
    
    def handle_stream_ready(self):
        self.connection_timer.stop()
        self.set_status("Conectado", "#00FF00")
        #self.status_label.show()
        self.status_connected_timer.start(5000)

    def handle_stream_error(self):
        self.set_status("SIN SEÑAL", "red")

    def handle_channel_changed(self):
        selected_data = self.cam_selector.currentData()
        new_channel = selected_data if selected_data else "Vacío"
        if new_channel != self.current_channel:
            self.current_channel = new_channel
            self.stop_stream()
            if self.current_channel != "Vacío":
                self.play_stream("2")
            else:
                self.set_status("Desconectado", "red")
            self.parent_grid.save_current_mapping()

    def toggle_audio(self):
        pass

    def handle_reconnect(self):
        if self.current_channel == "Vacío":
            return
        self.play_stream("2")

    def handle_auto_reconnect(self):
        if self.current_channel == "Vacío":
            return
        self.play_stream("2")

    def handle_double_click(self):
        if self.current_channel != "Vacío":
            self.parent_grid.handle_camera_double_click(self)

    def close_and_release(self):
        self.stop_stream()
        self.setParent(None)
        self.deleteLater()
    
    def enterEvent(self, event):
        self.controls_widget.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.popup_open:
            self.controls_widget.hide()
        super().leaveEvent(event)

    def resizeEvent(self, event):
        self.controls_widget.setGeometry( 0,
        self.video_container.height() - 40,
        self.video_container.width(), 40)
        
        self.status_label.setGeometry(0, 0,
        self.video_container.width(),
        self.video_container.height())
        super().resizeEvent(event)
