from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QGridLayout,
)

from src.config import save_config
from src.main_view_tab_section.camera_widget import CameraWidget


class MainViewTab(QWidget):
    def __init__(self, config, parent=None):
        super().__init__(parent)

        self.config = config
        self.cameras = []
        self.maximized_cam = None

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(6, 6, 6, 6)

        # Grid selector
        self.top_bar = QHBoxLayout()

        self.grid_selector = QComboBox()
        self.grid_selector.setObjectName("grid_selector")
        self.grid_selector.addItems([
            "Grilla 1x1",
            "Grilla 2x2",
            "Grilla 3x3",
            "Grilla 4x4",
        ])

        initial_index = self.config.get("LAST_GRID_SIZE", 3) - 1
        self.grid_selector.setCurrentIndex(
            max(0, min(initial_index, 3))
        )
        self.grid_selector.currentIndexChanged.connect(
            self.change_grid_size
        )

        self.top_bar.addWidget(self.grid_selector)
        self.top_bar.addStretch()
        self.main_layout.addLayout(self.top_bar)

        # Camera grid
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(2)
        self.main_layout.addLayout(self.grid_layout)

        self.build_grid(self.config.get("LAST_GRID_SIZE", 3))

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

        saved_mapping = self.config.get(
            "GRID_MAPPINGS", {}
        ).get(str(size), [])

        total_slots = size * size

        for i in range(total_slots):
            if i < len(saved_mapping):
                initial_channel = saved_mapping[i]
            else:
                initial_channel = (
                    str(i + 1)
                    if (i + 1) <= self.config["TOTAL_CHANNELS"]
                    else "Vacío"
                )

            cam_widget = CameraWidget(
                i,
                initial_channel,
                self,
                self.config,
            )

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

    def stop_all_streams(self):
        for cam in self.cameras:
            cam.stop_stream()
