import subprocess
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage

class FFmpegThread(QThread):
    frame_ready = pyqtSignal(QImage)
    stream_ready = pyqtSignal()
    stream_error = pyqtSignal()

    def __init__(self, url, width, height):
        super().__init__()
        self.url = url
        self.width = width
        self.height = height
        self.process = None
        self.running = True

    def run(self):
        frame_size = self.width * self.height * 3
        try:
            self.process = subprocess.Popen(
                ["ffmpeg", "-rtsp_transport", "tcp", "-loglevel", "error", "-i", self.url, "-an", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            )
            first_frame = True
            while self.running:
                data = self.read_exactly(frame_size)
                if not data:
                    break
                image = QImage(data, self.width, self.height, self.width * 3, QImage.Format.Format_RGB888).copy()
                if first_frame:
                    self.stream_ready.emit()
                    first_frame = False
                self.frame_ready.emit(image)
        except Exception:
            self.stream_error.emit()

    def read_exactly(self, size):
        data = bytearray()
        while len(data) < size and self.running:
            chunk = self.process.stdout.read(size - len(data))
            if not chunk:
                return None
            data.extend(chunk)
        return bytes(data) if len(data) == size else None

    def stop(self):
        self.running = False
        if self.process:
            try:
                self.process.stdout.close()
            except Exception:
                pass
            try:
                self.process.kill()
            except Exception:
                pass
            self.process = None
