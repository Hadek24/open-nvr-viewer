from src.config import load_config, get_default_profile
from PyQt6.QtCore import Qt, QPoint, QEvent
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget
from PyQt6.QtGui import QCursor
from src.styles import main_windows_style
from src.title_bar import TitleBar
from src.status_bar import StatusBar
from src.main_view_tab import MainViewTab
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
        if self.config is None:
            self.config = get_default_profile()
            self.config["name"] = "--"
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
        self.main_view = MainViewTab(self.config) #Pestaña "Main View"
        self.tabs.addTab(self.main_view, "Main View")
        self.playback_view = QWidget() #Pestaña "Playback"
        self.tabs.addTab(self.playback_view, "Playback")
        self.playback_layout = QVBoxLayout(self.playback_view)
        self.configuration_view = ConfigurationTab() #Pestaña "Configuration"
        self.tabs.addTab(self.configuration_view, "Configuration")
        self.status_bar = StatusBar(self.config, self) #Barra de status
        self.main_layout.addWidget(self.status_bar)

        self.setStyleSheet(main_windows_style) #Encargando de insertar estilos a la APP

    def closeEvent(self, event):
        self.main_view.stop_all_streams()
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
