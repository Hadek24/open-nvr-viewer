from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QLabel
from src.video_thread import FFmpegThread
from src.video_frame import VideoFrame

class CameraWidget(QWidget):
    def __init__(self, slot_index, initial_channel, parent_grid, config):
        super().__init__()
        self.slot_index = slot_index
        self.current_channel = initial_channel
        self.parent_grid = parent_grid
        self.config = config
        self.ffmpeg_thread = None
        self.is_muted = True
        self.connection_timer = QTimer(self)
        self.connection_timer.setSingleShot(True)
        self.connection_timer.timeout.connect(self.handle_connection_timeout)
        self.init_ui()
        if self.current_channel != "Vacío":
            self.play_stream("2")

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        self.video_frame = VideoFrame(self)
        layout.addWidget(self.video_frame)
        controls_layout = QHBoxLayout()
        self.cam_selector = QComboBox()
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
        self.status_label = QLabel("Desconectado")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        controls_layout.addWidget(self.status_label)
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        self.setLayout(layout)

    def play_stream(self, stream_type):
        if self.current_channel == "Vacío":
            return
        self.stop_stream()
        self.status_label.setStyleSheet("color: orange; font-weight: bold;")
        self.status_label.setText("Conectando...")
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
        if self.ffmpeg_thread:
            self.ffmpeg_thread.stop()
            self.ffmpeg_thread.wait(1000)
            self.ffmpeg_thread = None
        self.video_frame.image = None
        self.video_frame.update()

    def handle_frame(self, image, thread):
        if thread is not self.ffmpeg_thread:
            return
        self.video_frame.set_image(image)

    def handle_connection_timeout(self):
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        self.status_label.setText("SIN SEÑAL")
        if self.ffmpeg_thread:
            self.ffmpeg_thread.stop()
            self.ffmpeg_thread.wait(1000)
            self.ffmpeg_thread = None
    
    def handle_stream_ready(self):
        self.connection_timer.stop()
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        self.status_label.setText("OK")

    def handle_stream_error(self):
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        self.status_label.setText("SIN SEÑAL")

    def handle_channel_changed(self):
        selected_data = self.cam_selector.currentData()
        new_channel = selected_data if selected_data else "Vacío"
        if new_channel != self.current_channel:
            self.current_channel = new_channel
            self.stop_stream()
            if self.current_channel != "Vacío":
                self.play_stream("2")
            else:
                self.status_label.setStyleSheet("color: red; font-weight: bold;")
                self.status_label.setText("Desconectado")
            self.parent_grid.save_current_mapping()

    def toggle_audio(self):
        pass

    def handle_reconnect(self):
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
