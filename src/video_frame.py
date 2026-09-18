from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QPainter
from PyQt6.QtWidgets import QWidget

class VideoFrame(QWidget):
    def __init__(self, parent_camera):
        super().__init__()
        self.parent_camera = parent_camera
        self.image = None
        self.setStyleSheet("background-color: black;")

    def set_image(self, image):
        self.image = image
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.GlobalColor.black)
        if self.image is None:
            return
        pixmap = QPixmap.fromImage(self.image)
        pixmap = pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        x = (self.width() - pixmap.width()) // 2
        y = (self.height() - pixmap.height()) // 2
        painter.drawPixmap(x, y, pixmap)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.parent_camera.handle_double_click()
