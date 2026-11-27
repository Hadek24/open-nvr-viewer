from src.config import (
    load_config,
    get_default_profile,
    get_active_profile,
    load_raw_config,
    save_raw_config,
    remove_legacy_grid_settings,
)
from src.user_manager import UserManager
from src.status_manager import StatusManager
from PyQt6.QtCore import Qt, QPoint, QEvent
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget
from PyQt6.QtGui import QCursor
from src.styles import main_windows_style
from src.app_window.title_bar import TitleBar
from src.app_window.status_bar import StatusBar
from src.main_view_tab import MainViewTab
from src.configuration_tab import ConfigurationTab

class MainWindow(QMainWindow):
    def __init__(self, session_user):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self._resize_edge = Qt.Edge(0)
        self._resize_start_pos = QPoint()
        self._resize_start_geometry = self.geometry()
        QApplication.instance().installEventFilter(self)
        self.resize(1280, 720)
        self.setMinimumSize(800, 500)
        self.session_user = dict(session_user)
        self.user_id = self.session_user["id"]
        self.username = self.session_user["username"]
        self.role = self.session_user["role"]

        # Each non-Superadmin account uses its assigned NVR profile.
        # Superadmin has no assigned profile by design, so it uses the
        # globally selected profile when one is configured.
        if self.role == "Superadmin":
            self.profile_id = get_active_profile()
        else:
            self.profile_id = self.session_user.get("assigned_profile")

        raw_config = load_raw_config()
        profiles = raw_config.get("profiles", {}) if isinstance(raw_config, dict) else {}
        if not self.profile_id or self.profile_id not in profiles:
            self.profile_id = next(iter(profiles), None)

        self.config = load_config(self.profile_id) if self.profile_id else None
        if self.config is None:
            self.config = get_default_profile()
            self.config["name"] = "--"
            self.profile_id = self.profile_id or "nvr-principal"

        # Migrate any remaining legacy grid settings for this authenticated UUID
        # before removing them from config.json. Existing status entries win.
        if isinstance(raw_config, dict):
            StatusManager().migrate_legacy_grid_state(self.user_id, raw_config)
            if remove_legacy_grid_settings(raw_config):
                save_raw_config(raw_config)

        self.config.pop("LAST_GRID_SIZE", None)
        self.config.pop("GRID_MAPPINGS", None)
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
        self.main_view = MainViewTab(
            self.config,
            self.user_id,
            self.profile_id,
        ) # Pestaña "Main View"
        self.tabs.addTab(self.main_view, "Main View")
        self.playback_view = QWidget() #Pestaña "Playback"
        self.tabs.addTab(self.playback_view, "Playback")
        self.playback_layout = QVBoxLayout(self.playback_view)
        self.configuration_view = ConfigurationTab(self.user_id) #Pestaña "Configuration"
        self.tabs.addTab(self.configuration_view, "Configuration")
        self.status_bar = StatusBar(self.config, self.username, self) #Barra de status
        self.main_layout.addWidget(self.status_bar)

        self.setStyleSheet(main_windows_style) #Encargando de insertar estilos a la APP

    def logout(self):
        """Stop the current session and return to the local login screen."""
        from src.auth_dialogs import LoginDialog

        self.main_view.stop_all_streams()
        self.hide()
        dialog = LoginDialog(UserManager())
        if dialog.exec():
            replacement = MainWindow(dialog.session_user)
            replacement.show()
            self._replacement_window = replacement
            self.close()
        else:
            QApplication.instance().quit()

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
