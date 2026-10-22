"""Configuration file management section for Open NVR Viewer."""

import os
import sys

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox,
    QScrollArea,
)

from src.config import (
    create_config,
    get_config_path,
    get_config_dir,
    delete_config,
)

from src.styles import (
    configuration_action_button_style,
    configuration_scroll_area_style,
    configuration_section_title_style,
    configuration_section_description_style,
    configuration_subsection_title_style,
    configuration_field_label_style,
    configuration_separator_style,
    configuration_status_found_style,
    configuration_status_not_found_style,
)

class ConfigFileSection(QWidget):
    """Create, inspect, delete, and locate the application config file."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.Shape.StyledPanel)
        self.scroll_area.setStyleSheet(configuration_scroll_area_style)

        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(10)
        self.scroll_area.setWidget(self.content)
        self.main_layout.addWidget(self.scroll_area)

        self.title = QLabel("Config File")
        self.title.setStyleSheet(configuration_section_title_style)

        self.description = QLabel(
            "Manage the configuration file used by Open NVR Viewer. "
            "Connection profiles are stored in this file."
        )
        self.description.setWordWrap(True)
        self.description.setStyleSheet(configuration_section_description_style)

        self.content_layout.addWidget(self.title)
        self.content_layout.addWidget(self.description)

        # Separador entre el título principal y el contenido.
        self.separator_1 = QLabel()
        self.separator_1.setFixedHeight(1)
        self.separator_1.setStyleSheet(configuration_separator_style)

        self.content_layout.addSpacing(8)
        self.content_layout.addWidget(self.separator_1)
        self.content_layout.addSpacing(8)

        self.status_title = QLabel("Configuration File Check")
        self.status_title.setStyleSheet(configuration_subsection_title_style)

        self.config_status_indicator = QLabel()
        self.content_layout.addWidget(self.status_title)

        status_layout = QHBoxLayout()
        self.status_label = QLabel("Status:")
        self.status_label.setStyleSheet(configuration_field_label_style)

        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.config_status_indicator)
        self.content_layout.addLayout(status_layout)
        
        # Separador entre el título y el estado del archivo.
        self.separator_2 = QLabel()
        self.separator_2.setFixedHeight(1)
        self.separator_2.setStyleSheet(configuration_separator_style)
        
        self.content_layout.addSpacing(8)
        self.content_layout.addWidget(self.separator_2)
        self.content_layout.addSpacing(8)

        # --- Nueva subsección de acciones ---
        self.actions_title = QLabel("Configuration File Management")
        self.actions_title.setStyleSheet(configuration_subsection_title_style)
        self.content_layout.addWidget(self.actions_title)

        self.content_layout.addSpacing(8)
        self._add_action_row(
            "Generate configuration file:",
            "Generate",
            self.generate_config_file,
        )
        self._add_action_row(
            "Delete configuration file:",
            "Delete",
            self.delete_config_file,
        )
        self._add_action_row(
            "Open configuration directory:",
            "Open",
            self.open_config_directory,
        )
        self.content_layout.addStretch()

        self.update_config_status()

    def _add_action_row(self, label_text, button_text, callback):
        row = QHBoxLayout()

        label = QLabel(label_text)
        label.setFixedWidth(190)
        label.setStyleSheet(configuration_field_label_style)

        button = QPushButton(button_text)
        button.setFixedWidth(100)
        button.setStyleSheet(configuration_action_button_style)
        button.clicked.connect(callback)

        row.addWidget(label)
        row.addWidget(button)
        row.addStretch()
        self.content_layout.addLayout(row)

    def update_config_status(self):
        """Refresh the indicator showing whether the config file exists."""
        if os.path.exists(get_config_path()):
            self.config_status_indicator.setText("● Found")
            self.config_status_indicator.setStyleSheet(
                configuration_status_found_style
            )
        else:
            self.config_status_indicator.setText("● Not Found")
            self.config_status_indicator.setStyleSheet(
                configuration_status_not_found_style
            )

    def generate_config_file(self):
        """Create the configuration file if it does not already exist."""
        if os.path.exists(get_config_path()):
            QMessageBox.information(
                self,
                "Configuration File",
                "The configuration file already exists.",
            )
            return

        create_config()
        self.update_config_status()
        QMessageBox.information(
            self,
            "Configuration File",
            "The configuration file was created successfully.",
        )

    def delete_config_file(self):
        """Confirm and delete the configuration file, then restart."""
        reply = QMessageBox.warning(
            self,
            "Delete Configuration",
            "Are you sure?\n\n"
            "This will delete all profile configuration information. "
            "This action cannot be undone",
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )

        if reply != QMessageBox.StandardButton.Ok:
            return

        if not delete_config():
            QMessageBox.critical(
                self,
                "Error",
                "The configuration could not be deleted.",
            )
            return

        QMessageBox.information(
            self,
            "Restart Required",
            "The application needs to restart.",
            QMessageBox.StandardButton.Ok,
        )
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def open_config_directory(self):
        """Open the configuration directory, creating it if necessary."""
        config_dir = get_config_dir()
        os.makedirs(config_dir, exist_ok=True)

        if sys.platform == "win32":
            os.startfile(config_dir)
        else:
            os.system(f'xdg-open "{config_dir}"')
