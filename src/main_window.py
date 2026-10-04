from src.config import load_config, save_config
from PyQt6.QtCore import Qt, QPoint, QEvent
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QGridLayout, QTabWidget, QLabel, QPushButton, QSizeGrip
from PyQt6.QtGui import QPainter, QLinearGradient, QColor, QCursor
from src.camera_widget import CameraWidget
from src.styles import main_windows_style
from src.title_bar import TitleBar
from src.status_bar import StatusBar
from src.configuration_tab import ConfigurationTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self._resize_edge = Qt.Edge(0)
        self._resize_start_pos = QPoint()
        self._resize_start_geometry = self.geometry()
        QApplication.instance().installEventFilter(self)
        self.resize(1280, 720)
        self.setMinimumSize(800, 500)
        self.config = load_config()
        self.cameras = []
        self.maximized_cam = None
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.title_bar = TitleBar(self)
        self.main_layout.addWidget(self.title_bar)
        self.main_layout.addSpacing(6)
        
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        self.main_view = QWidget() #Pestaña "Main View"
        self.tabs.addTab(self.main_view, "Main View")
        self.main_view_layout = QVBoxLayout(self.main_view)
        self.main_view_layout.setContentsMargins(6, 6, 6, 6)
        self.playback_view = QWidget() #Pestaña "Playback"
        self.tabs.addTab(self.playback_view, "Playback")
        self.playback_layout = QVBoxLayout(self.playback_view)
        self.configuration_view = ConfigurationTab() #Pestaña "Configuration"
        self.tabs.addTab(self.configuration_view, "Configuration")
        self.status_bar = StatusBar(self.config, self) #Barra de status
        self.main_layout.addWidget(self.status_bar)
        self.top_bar = QHBoxLayout()
        self.grid_selector = QComboBox()
        self.grid_selector.setObjectName("grid_selector")
        self.grid_selector.addItems(["Grilla 1x1", "Grilla 2x2", "Grilla 3x3", "Grilla 4x4"])
        initial_index = self.config.get("LAST_GRID_SIZE", 3) - 1
        self.grid_selector.setCurrentIndex(max(0, min(initial_index, 3)))
        self.grid_selector.currentIndexChanged.connect(self.change_grid_size)
        self.top_bar.addWidget(self.grid_selector)
        self.top_bar.addStretch()
        self.main_view_layout.addLayout(self.top_bar) #Selector de grilla
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(2)
        self.main_view_layout.addLayout(self.grid_layout) #Camaras
        self.build_grid(self.config.get("LAST_GRID_SIZE", 3))
        self.setStyleSheet(main_windows_style) #Encargando de insertar estilos a la APP

    def save_current_mapping(self):
        current_size = self.grid_selector.currentText()
        size_num = 1
        if "2x2" in current_size:
            size_num = 2
        elif "3x3" in current_size:
            size_num = 3
        elif "4x4" in current_size:
            size_num = 4
        mapping = [cam.current_channel for cam in self.cameras]
        self.config["LAST_GRID_SIZE"] = size_num
        self.config["GRID_MAPPINGS"][str(size_num)] = mapping
        save_config(self.config)

    def build_grid(self, size):
        self.maximized_cam = None
        for cam in self.cameras:
            cam.close_and_release()
        self.cameras.clear()
        saved_mapping = self.config.get("GRID_MAPPINGS", {}).get(str(size), [])
        total_slots = size * size
        for i in range(total_slots):
            if i < len(saved_mapping):
                initial_channel = saved_mapping[i]
            else:
                initial_channel = str(i + 1) if (i + 1) <= self.config["TOTAL_CHANNELS"] else "Vacío"
            cam_widget = CameraWidget(i, initial_channel, self, self.config)
            row = i // size
            col = i % size
            self.grid_layout.addWidget(cam_widget, row, col)
            self.cameras.append(cam_widget)
        self.save_current_mapping()

    def change_grid_size(self):
        text = self.grid_selector.currentText()
        if "1x1" in text:
            self.build_grid(1)
        elif "2x2" in text:
            self.build_grid(2)
        elif "3x3" in text:
            self.build_grid(3)
        elif "4x4" in text:
             self.build_grid(4)

    def handle_camera_double_click(self, clicked_cam):
        if self.maximized_cam is None:
            self.maximized_cam = clicked_cam
            self.grid_selector.setEnabled(False)
            for cam in self.cameras:
                if cam != clicked_cam:
                    cam.setVisible(False)
            clicked_cam.play_stream("1")
        else:
            for cam in self.cameras:
                cam.setVisible(True)
            self.maximized_cam.play_stream("2")
            self.maximized_cam = None
            self.grid_selector.setEnabled(True)

    def closeEvent(self, event):
        for cam in self.cameras:
            cam.stop_stream()
        event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def get_resize_edges(self, pos):
        if self.isMaximized():
            return Qt.Edge(0)
        margin = 8
        rect = self.rect()
        edges = Qt.Edge(0)
        if pos.x() <= margin:
            edges |= Qt.Edge.LeftEdge
        elif pos.x() >= rect.width() - margin:
            edges |= Qt.Edge.RightEdge
        if pos.y() <= margin:
            edges |= Qt.Edge.TopEdge
        elif pos.y() >= rect.height() - margin:
            edges |= Qt.Edge.BottomEdge
        return edges

    def update_resize_cursor(self, edges):
        if edges in (Qt.Edge.LeftEdge, Qt.Edge.RightEdge):
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif edges in (Qt.Edge.TopEdge, Qt.Edge.BottomEdge):
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        elif edges in (Qt.Edge.TopEdge | Qt.Edge.LeftEdge,
                       Qt.Edge.BottomEdge | Qt.Edge.RightEdge):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif edges in (Qt.Edge.TopEdge | Qt.Edge.RightEdge,
                       Qt.Edge.BottomEdge | Qt.Edge.LeftEdge):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        else:
            self.unsetCursor()

    def eventFilter(self, obj, event):
        if obj is not self and (not isinstance(obj, QWidget) or not self.isAncestorOf(obj)):
            return super().eventFilter(obj, event)
        if self.isMaximized():
            return super().eventFilter(obj, event)
        if event.type() == QEvent.Type.MouseMove:
            pos = self.mapFromGlobal(QCursor.pos())
            if self._resize_edge:
                current_pos = QCursor.pos()
                delta = current_pos - self._resize_start_pos
                geometry = self._resize_start_geometry
                left = geometry.left()
                top = geometry.top()
                width = geometry.width()
                height = geometry.height()
                if self._resize_edge & Qt.Edge.LeftEdge:
                    new_left = left + delta.x()
                    new_width = width - delta.x()
                    if new_width >= self.minimumWidth():
                        left = new_left
                        width = new_width
                if self._resize_edge & Qt.Edge.RightEdge:
                    width = max(
                        self.minimumWidth(),
                        width + delta.x())
                if self._resize_edge & Qt.Edge.TopEdge:
                    new_top = top + delta.y()
                    new_height = height - delta.y()
                    if new_height >= self.minimumHeight():
                        top = new_top
                        height = new_height
                if self._resize_edge & Qt.Edge.BottomEdge:
                     height = max(
                        self.minimumHeight(),
                        height + delta.y())
                self.setGeometry(left, top, width, height)
                return True
            edges = self.get_resize_edges(pos)
            self.update_resize_cursor(edges)
        elif event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                pos = self.mapFromGlobal(QCursor.pos())
                edges = self.get_resize_edges(pos)
                if edges:
                    self._resize_edge = edges
                    self._resize_start_pos = QCursor.pos()
                    self._resize_start_geometry = self.geometry()
                    return True
        elif event.type() == QEvent.Type.MouseButtonRelease:
            if event.button() == Qt.MouseButton.LeftButton:
                if self._resize_edge:
                    self._resize_edge = Qt.Edge(0)
                    self.update_resize_cursor(
                        self.get_resize_edges(
                            self.mapFromGlobal(QCursor.pos())))
                    return True
        return super().eventFilter(obj, event)
