import os
import sys
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QLineEdit, QComboBox, QScrollArea, QListWidget, QMessageBox, QInputDialog, QDialog, QGridLayout
from PyQt6.QtCore import Qt
from src.config import (
    create_config,
    get_config_path,
    get_config_dir,
    delete_config,
    create_profile,
    update_profile,
    get_profiles, 
    delete_profile,
    get_active_profile, 
    set_active_profile, 
    get_default_profile, 
    get_nvr_password, 
    set_nvr_password, 
    generate_profile_id, 
    validate_profile,
    set_active_profile,
    )
from src.connection_test import ConnectionTestThread

class ConnectionTestDialog(QDialog):
    def __init__(self, profile_name, parent=None):
        super().__init__(parent)

        self.setWindowTitle("NVR Connection Test")
        self.setMinimumWidth(480)

        layout = QVBoxLayout(self)

        title = QLabel(f"Connection diagnostics: {profile_name}")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)

        self.results = {}

        tests = [
            ("ping", "Ping"),
            ("port", "RTSP TCP Port"),
            ("credentials", "RTSP Credentials"),
            ("rtsp", "RTSP Connection"),
            ("frame", "Video Frame Received"),
        ]

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)

        for row, (key, label_text) in enumerate(tests):
            label = QLabel(label_text)
            status = QLabel("Pending")
            status.setStyleSheet("color: #9CA3AF;")

            grid.addWidget(label, row, 0)
            grid.addWidget(status, row, 1)

            self.results[key] = status

        layout.addLayout(grid)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        layout.addWidget(self.close_button)

    def update_result(self, key, success, message):
        status = self.results[key]

        if success:
            status.setText(f"✓ OK — {message}")
            status.setStyleSheet("color: #3FB950;")
        else:
            status.setText(f"✗ Failed — {message}")
            status.setStyleSheet("color: #F85149;")

class ConfigurationTab(QWidget):
    def __init__(self):
        super().__init__()

        self.editing_profile_id = None
        self.editing_profile_name = None

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(6, 6, 6, 6)
        self.layout.setSpacing(6)

        self.left_panel = QWidget()
        self.left_panel.setObjectName("configuration_left")

        self.right_panel = QWidget()
        self.right_panel.setObjectName("configuration_right")

        self.right_panel_layout = QVBoxLayout(self.right_panel)
        self.right_panel_layout.setContentsMargins(0, 0, 0, 0)

        self.right_scroll = QScrollArea()
        self.right_scroll.setWidgetResizable(True)
        self.right_scroll.setFrameShape(QScrollArea.Shape.StyledPanel)
        self.right_scroll.setStyleSheet("""
            QScrollArea {border: 1px solid white; border-radius: 6px; background: transparent;}
            QScrollArea > QWidget > QWidget {background: transparent;}""")

        self.right_content = QWidget()
        self.right_layout = QVBoxLayout(self.right_content)
        self.right_layout.setContentsMargins(20, 20, 20, 20)
        self.right_layout.setSpacing(10)

        self.right_scroll.setWidget(self.right_content)
        self.right_panel_layout.addWidget(self.right_scroll)
        
        #Subseccion NVR Configuration
        self.nvr_title = QLabel("NVR Configuration")
        self.nvr_title.setStyleSheet("""
            QLabel {color: white; font-size: 16px; font-weight: bold; border: none;}""")

        self.nvr_description = QLabel(
            "This application requires a configuration file to store its settings. "
            "If no configuration file is found, generate one before creating a "
            "connection profile.")
        
        self.nvr_description.setWordWrap(True)
        self.nvr_description.setStyleSheet("""
            QLabel {color: #CCCCCC; font-size: 13px; border: none;}""")

        # Separador
        self.separator_1 = QLabel()
        self.separator_1.setFixedHeight(1)
        self.separator_1.setStyleSheet("""
            QLabel {background-color: #555555; border: none;}""")

        self.configuration_file_layout = QHBoxLayout()
        self.configuration_file_title = QLabel("Configuration File")
        self.configuration_file_title.setStyleSheet("""
            QLabel {color: white; font-size: 14px; font-weight: bold; border: none;}""")

        self.config_status_indicator = QLabel("● Found")
        self.config_status_indicator.setStyleSheet("""
            QLabel {color: #00FF00; font-size: 14px; font-weight: bold; border: none;}""")

        self.configuration_file_layout.addWidget(self.configuration_file_title)
        self.configuration_file_layout.addStretch()
        self.configuration_file_layout.addWidget(self.config_status_indicator)

        self.action_button_style = """
            QPushButton {color: white; font-size: 13px; font-weight: bold; padding: 6px 12px; border: 1px solid #666666; border-radius: 4px; background-color: #333333;}
            QPushButton:hover {background-color: #444444; border: 1px solid #888888;}
            QPushButton:pressed {background-color: #555555;}"""

        # Configuration file actions
        self.generate_config_label = QLabel("Generate configuration file:")
        self.generate_config_label.setFixedWidth(190)
        self.generate_config_label.setStyleSheet("""
            QLabel {color: white; font-size: 14px; border: none;}""")

        self.generate_config_button = QPushButton("Generate")
        self.generate_config_button.setFixedWidth(100)
        self.generate_config_button.setStyleSheet(self.action_button_style)
        self.generate_config_button.clicked.connect(self.generate_config_file)
        self.generate_config_layout = QHBoxLayout()
        self.generate_config_layout.addWidget(self.generate_config_label)
        self.generate_config_layout.addWidget(self.generate_config_button)
        self.generate_config_layout.addStretch()

        self.delete_config_label = QLabel("Delete configuration file:")
        self.delete_config_label.setFixedWidth(190)
        self.delete_config_label.setStyleSheet("""
            QLabel {color: white; font-size: 14px; border: none;}""")

        self.delete_config_button = QPushButton("Delete")
        self.delete_config_button.setFixedWidth(100)
        self.delete_config_button.setStyleSheet(self.action_button_style)
        self.delete_config_button.clicked.connect(self.delete_config_file)
        self.delete_config_layout = QHBoxLayout()
        self.delete_config_layout.addWidget(self.delete_config_label)
        self.delete_config_layout.addWidget(self.delete_config_button)
        self.delete_config_layout.addStretch()

        self.open_config_label = QLabel("Open configuration directory:")
        self.open_config_label.setFixedWidth(190)
        self.open_config_label.setStyleSheet("""
            QLabel {color: white; font-size: 14px; border: none;}""")

        self.open_config_button = QPushButton("Open")
        self.open_config_button.setFixedWidth(100)
        self.open_config_button.setStyleSheet(self.action_button_style)
        self.open_config_button.clicked.connect(self.open_config_directory)
        self.open_config_layout = QHBoxLayout()
        self.open_config_layout.addWidget(self.open_config_label)
        self.open_config_layout.addWidget(self.open_config_button)
        self.open_config_layout.addStretch()

        self.right_layout.addWidget(self.nvr_title)
        self.right_layout.addWidget(self.nvr_description)
        self.right_layout.addSpacing(8)

        self.right_layout.addWidget(self.separator_1)
        self.right_layout.addSpacing(8)

        self.right_layout.addLayout(self.configuration_file_layout)
        self.right_layout.addLayout(self.generate_config_layout)
        self.right_layout.addLayout(self.delete_config_layout)
        self.right_layout.addLayout(self.open_config_layout)

        # Separador - Connection
        self.separator_2 = QLabel()
        self.separator_2.setFixedHeight(1)
        self.separator_2.setStyleSheet("""
            QLabel {background-color: #555555; border: none;}""")

        self.connection_title = QLabel("NVR Connection Configuration")
        self.connection_title.setStyleSheet("""
            QLabel {color: white; font-size: 14px; font-weight: bold; border: none;}""")

        self.right_layout.addSpacing(8)
        self.right_layout.addWidget(self.separator_2)
        self.right_layout.addSpacing(8)
        self.right_layout.addWidget(self.connection_title)

        self.connection_field_style = """
            QLineEdit {color: white; font-size: 14px; padding: 5px 8px; border: 1px solid #666666; border-radius: 4px; background-color: #333333;}
            QLineEdit:focus {border: 1px solid #888888;}"""

        self.editing_profile_label = QLabel("")
        self.editing_profile_label.setStyleSheet(
            "font-weight: bold; color: #d97706;"
        )
        self.editing_profile_label.hide()

        self.right_layout.addWidget(self.editing_profile_label)

        self.connection_fields = [
            ("Profile name:", "profile_name"),
            ("Username NVR:", "nvr_username"),
            ("Password NVR:", "nvr_password"),
            ("Confirm password:", "nvr_password_confirm"),
            ("NVR IP:", "nvr_ip"),
            ("NVR Port:", "nvr_port"),
            ("NVR channels:", "nvr_channels"),]

        for label_text, field_name in self.connection_fields:
            row = QHBoxLayout()
            label = QLabel(label_text)
            label.setFixedWidth(190)
            label.setStyleSheet("""
                QLabel {color: white; font-size: 14px; border: none;}""")

            field = QLineEdit()
            field.setFixedWidth(250)
            field.setStyleSheet(self.connection_field_style)

            if field_name in ("nvr_password", "nvr_password_confirm"):
                field.setEchoMode(QLineEdit.EchoMode.Password)

            setattr(self, field_name, field)

            row.addWidget(label)
            row.addWidget(field)
            row.addStretch()

            self.right_layout.addLayout(row)
        
        self.create_profile_button = QPushButton("Create")
        self.create_profile_button.clicked.connect(self.create_new_profile)
        self.create_profile_button.setFixedWidth(100)
        self.create_profile_button.setStyleSheet(self.action_button_style)
        
        self.save_profile_button = QPushButton("Save Changes")
        self.save_profile_button.clicked.connect(self.save_edited_profile)
        self.save_profile_button.setFixedWidth(120)
        self.save_profile_button.setStyleSheet(self.action_button_style)
        self.save_profile_button.hide()

        self.cancel_edit_button = QPushButton("Cancel")
        self.cancel_edit_button.clicked.connect(self.cancel_profile_edit)
        self.cancel_edit_button.setFixedWidth(100)
        self.cancel_edit_button.setStyleSheet(self.action_button_style)
        self.cancel_edit_button.hide()

        self.create_profile_layout = QHBoxLayout()
        self.create_profile_layout.setContentsMargins(0, 8, 0, 0)
        self.create_profile_layout.setSpacing(10)
        self.create_profile_layout.addSpacing(200)
        self.create_profile_layout.addWidget(self.create_profile_button)
        self.create_profile_layout.addWidget(self.save_profile_button)
        self.create_profile_layout.addWidget(self.cancel_edit_button)
        self.create_profile_layout.addStretch()

        self.right_layout.addLayout(self.create_profile_layout)

        # Separador - Manage Connection Profiles
        self.separator_3 = QLabel()
        self.separator_3.setFixedHeight(1)
        self.separator_3.setStyleSheet("""
            QLabel {background-color: #555555; border: none;}""")

        self.profile_management_title = QLabel("Manage Connection Profiles")
        self.profile_management_title.setStyleSheet("""
            QLabel {color: white; font-size: 14px; font-weight: bold; border: none;}""")

        self.right_layout.addSpacing(12)
        self.right_layout.addWidget(self.separator_3)
        self.right_layout.addSpacing(8)
        self.right_layout.addWidget(self.profile_management_title)
        
        self.active_profile_layout = QHBoxLayout()

        self.active_profile_label = QLabel("Active Profile:")
        self.active_profile_label.setFixedWidth(190)
        self.active_profile_label.setStyleSheet("""
            QLabel {color: white; font-size: 14px; border: none;}""")

        self.active_profile_combo = QComboBox()
        self.active_profile_combo.setFixedWidth(250)

        self.activate_profile_button = QPushButton("Activate")
        self.activate_profile_button.clicked.connect(self.activate_profile)
        self.activate_profile_button.setFixedWidth(100)
        self.activate_profile_button.setStyleSheet(self.action_button_style)

        self.active_profile_layout.addWidget(self.active_profile_label)
        self.active_profile_layout.addWidget(self.active_profile_combo)
        self.active_profile_layout.addSpacing(10)
        self.active_profile_layout.addWidget(self.activate_profile_button)
        self.active_profile_layout.addStretch()

        self.right_layout.addLayout(self.active_profile_layout)

        # Profile Management
        self.profile_list_title = QLabel("Profile Management")
        self.profile_list_title.setStyleSheet("""
            QLabel {color: white; font-size: 14px; font-weight: bold; border: none;}""")

        self.right_layout.addSpacing(10)
        self.right_layout.addWidget(self.profile_list_title)
        self.profile_list = QListWidget()
        self.profile_list.setFixedWidth(320)
        self.profile_list.setMinimumHeight(120)
        self.profile_list.setStyleSheet("""
            QListWidget {color: white; font-size: 14px; border: 1px solid #666666; border-radius: 4px; background-color: #333333; padding: 4px;}
            QListWidget::item {padding: 6px;}
            QListWidget::item:selected {background-color: #555555;}""")

        self.right_layout.addWidget(self.profile_list)

        self.profile_actions_layout = QHBoxLayout()
        self.profile_actions_layout.setContentsMargins(0, 8, 0, 0)
        self.profile_actions_layout.setSpacing(10)

        self.delete_profile_button = QPushButton("Delete")
        self.edit_profile_button = QPushButton("Edit")
        self.test_profile_button = QPushButton("Test")
        
        self.delete_profile_button.clicked.connect(self.delete_selected_profile)
        self.edit_profile_button.clicked.connect(self.edit_selected_profile)
        self.test_profile_button.clicked.connect(self.test_selected_profile)

        self.delete_profile_button.setFixedWidth(100)
        self.edit_profile_button.setFixedWidth(100)
        self.test_profile_button.setFixedWidth(100)

        self.delete_profile_button.setStyleSheet(self.action_button_style)
        self.edit_profile_button.setStyleSheet(self.action_button_style)
        self.test_profile_button.setStyleSheet(self.action_button_style)

        self.profile_actions_layout.addWidget(self.delete_profile_button)
        self.profile_actions_layout.addWidget(self.edit_profile_button)
        self.profile_actions_layout.addWidget(self.test_profile_button)
        self.profile_actions_layout.addStretch()

        self.right_layout.addLayout(self.profile_actions_layout)
        
        self.left_panel.setStyleSheet("#configuration_left { border: 1px solid white; border-radius: 6px;}")
        #self.right_panel.setStyleSheet("#configuration_right { border: 1px solid white; border-radius: 6px;}")

        self.layout.addWidget(self.left_panel, 1)
        self.layout.addWidget(self.right_panel, 3)

        # Panel izquierdo
        self.left_layout = QVBoxLayout(self.left_panel)

        self.configuration_title = QLabel("Configuration")
        self.configuration_title.setStyleSheet("""
            QLabel {color: white; font-size: 18px; font-weight: bold; border: none;}""")

        self.menu_button_style = """
            QPushButton {color: white; font-size: 14px; font-weight: bold; text-align: left; padding: 8px 12px; border: 1px solid #666666; border-radius: 4px; background-color: #333333;}
            QPushButton:hover {background-color: #444444; border: 1px solid #888888;}
            QPushButton:pressed {background-color: #555555;}"""

        self.nvr_button = QPushButton("NVR")
        self.nvr_button.setStyleSheet(self.menu_button_style)
        self.option1_button = QPushButton("Opción 1")
        self.option1_button.setStyleSheet(self.menu_button_style)
        self.option2_button = QPushButton("Opción 2")
        self.option2_button.setStyleSheet(self.menu_button_style)
        self.option3_button = QPushButton("Opción 3")
        self.option3_button.setStyleSheet(self.menu_button_style)
        self.option4_button = QPushButton("Opción 4")
        self.option4_button.setStyleSheet(self.menu_button_style)
        self.option5_button = QPushButton("Opción 5")
        self.option5_button.setStyleSheet(self.menu_button_style)

        self.left_layout.addWidget(self.configuration_title)
        self.left_layout.addWidget(self.nvr_button)
        self.left_layout.addWidget(self.option1_button)
        self.left_layout.addWidget(self.option2_button)
        self.left_layout.addWidget(self.option3_button)
        self.left_layout.addWidget(self.option4_button)
        self.left_layout.addWidget(self.option5_button)
        self.left_layout.addStretch()
        self.load_profiles()
        self.update_config_status()

    def update_config_status(self):
        config_path = get_config_path()

        if os.path.exists(config_path):
            self.config_status_indicator.setText("● Found")
            self.config_status_indicator.setStyleSheet("""
                QLabel {color: #00FF00; font-size: 14px; font-weight: bold; border: none;}""")
        else:
            self.config_status_indicator.setText("● Not Found")
            self.config_status_indicator.setStyleSheet("""
                QLabel {color: #F85149; font-size: 14px; font-weight: bold; border: none;}""")

    def generate_config_file(self):
        config_path = get_config_path()

        if os.path.exists(config_path):
            QMessageBox.information(
                self,
                "Configuration File",
                "The configuration file already exists."
            )
            return

        create_config()
        self.update_config_status()

        QMessageBox.information(
            self,
            "Configuration File",
            "The configuration file was created successfully."
        )

    def delete_config_file(self):
        reply = QMessageBox.warning(
            self,
            "Delete Configuration",
            "Are you sure?\n\n"
            "This will delete all profile configuration information. This action cannot be undone",
            QMessageBox.StandardButton.Ok
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel
        )

        if reply != QMessageBox.StandardButton.Ok:
            return

        if not delete_config():
            QMessageBox.critical(
                self,
                "Error",
                "The configuration could not be deleted."
            )
            return

        QMessageBox.information(
            self,
            "Restart Required",
            "The application needs to restart.",
            QMessageBox.StandardButton.Ok
        )

        os.execv(
            sys.executable,
            [sys.executable] + sys.argv
        )

    def open_config_directory(self):
        """
        Funcion: Permite abrir la carpeta donde esta el config.json
        Si no existe, la crea.
        """
        config_dir = get_config_dir()
        os.makedirs(config_dir, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(config_dir)
        else:
            os.system(f'xdg-open "{config_dir}"')

    def load_profiles(self):
        """
        Carga los perfiles disponibles en los controles de la interfaz.
        """
        profiles = get_profiles()
        active_profile = get_active_profile()

        self.active_profile_combo.clear()
        self.profile_list.clear()

        for profile_id, profile in profiles.items():
            profile_name = profile.get("name", profile_id)

            self.active_profile_combo.addItem(
                profile_name,
                profile_id
            )

            self.profile_list.addItem(profile_name)
            item = self.profile_list.item(self.profile_list.count() - 1)
            item.setData(Qt.ItemDataRole.UserRole, profile_id)

        # Seleccionar el perfil activo.
        if active_profile:
            index = self.active_profile_combo.findData(active_profile)

            if index >= 0:
                self.active_profile_combo.setCurrentIndex(index)

    def edit_selected_profile(self):
        """
        Verifica la contraseña actual y carga los datos del perfil
        seleccionado para su edición.
        """
        selected_item = self.profile_list.currentItem()

        if selected_item is None:
            QMessageBox.information(
                self,
                "Edit Profile",
                "Please select a profile to edit."
            )
            return

        profile_id = selected_item.data(Qt.ItemDataRole.UserRole)
        profile_name = selected_item.text()

        current_password = get_nvr_password(profile_id)

        if not current_password:
            QMessageBox.warning(
                self,
                "Edit Profile",
                "No password is stored for this profile. "
                "The profile cannot be edited."
            )
            return

        password, accepted = QInputDialog.getText(
            self,
            "Verify Password",
            f"Enter the current NVR password for '{profile_name}':",
            QLineEdit.EchoMode.Password
        )

        if not accepted:
            return

        if password != current_password:
            QMessageBox.warning(
                self,
                "Edit Profile",
                "The password is incorrect."
            )
            return

        profiles = get_profiles()
        profile_data = profiles.get(profile_id)

        if profile_data is None:
            QMessageBox.critical(
                self,
                "Edit Profile",
                "The selected profile could not be found."
            )
            return

        self.editing_profile_id = profile_id
        self.editing_profile_name = profile_name

        self.profile_name.setText(profile_data.get("name", ""))
        self.nvr_username.setText(profile_data.get("NVR_USER", ""))
        self.nvr_password.setText(current_password)
        self.nvr_password_confirm.setText(current_password)
        self.nvr_ip.setText(profile_data.get("NVR_IP", ""))
        self.nvr_port.setText(str(profile_data.get("NVR_PORT", "")))
        self.nvr_channels.setText(
            str(profile_data.get("TOTAL_CHANNELS", ""))
        )

        self.editing_profile_label.setText(
            f"Editing profile: {profile_name}"
        )
        self.editing_profile_label.show()

        self.create_profile_button.hide()
        self.save_profile_button.show()
        self.cancel_edit_button.show()

        self.right_scroll.ensureWidgetVisible(self.editing_profile_label)


    def test_selected_profile(self):
        """
        Obtiene la configuración del perfil seleccionado
        y ejecuta las pruebas de conectividad.
        """
        selected_item = self.profile_list.currentItem()

        if selected_item is None:
            QMessageBox.information(
                self,
                "Test Profile",
                "Please select a profile to test."
            )
            return

        profile_id = selected_item.data(Qt.ItemDataRole.UserRole)
        profiles = get_profiles()
        profile_data = profiles.get(profile_id)

        if profile_data is None:
            QMessageBox.warning(
                self,
                "Test Profile",
                "The selected profile could not be found."
            )
            return

        password = get_nvr_password(profile_id)

        if password is None:
            QMessageBox.warning(
                self,
                "Test Profile",
                "No password is stored for this profile."
            )
            return

        profile_name = profile_data.get("name", profile_id)

        self.test_dialog = ConnectionTestDialog(
            profile_name,
            self
        )
        self.test_dialog.show()

        self.test_thread = ConnectionTestThread(
            profile_data.get("NVR_IP", ""),
            profile_data.get("NVR_PORT", 0)
        )

        self.test_thread.result_ready.connect(
            self.show_connection_test_result
        )

        self.test_thread.start()


    def show_connection_test_result(self, test_name, success, message):
        test_keys = {
            "Ping": "ping",
            "Puerto TCP": "port",
        }

        key = test_keys.get(test_name)

        if key and hasattr(self, "test_dialog"):
            self.test_dialog.update_result(
                key,
                success,
                message
            )

    def save_edited_profile(self):
        """
        Guarda los cambios del perfil que se está editando.
        """
        profile_id = self.editing_profile_id

        if not profile_id:
            QMessageBox.warning(
                self,
                "Save Profile",
                "No profile is currently being edited."
            )
            return

        profile_name = self.profile_name.text().strip()
        nvr_user = self.nvr_username.text().strip()
        nvr_password = self.nvr_password.text()
        nvr_password_confirm = self.nvr_password_confirm.text()
        nvr_ip = self.nvr_ip.text().strip()
        nvr_port = self.nvr_port.text().strip()
        nvr_channels = self.nvr_channels.text().strip()

        if not nvr_password:
            QMessageBox.warning(
                self,
                "Save Profile",
                "The NVR password is required."
            )
            return

        if not nvr_password_confirm:
            QMessageBox.warning(
                self,
                "Save Profile",
                "Please confirm the NVR password."
            )
            return

        if any(char.isspace() for char in nvr_password):
            QMessageBox.warning(
                self,
                "Save Profile",
                "The password cannot contain spaces."
            )
            return

        if nvr_password != nvr_password_confirm:
            QMessageBox.warning(
                self,
                "Save Profile",
                "The passwords do not match."
            )
            return

        valid, error = validate_profile(
            profile_name,
            nvr_user,
            nvr_ip,
            nvr_port,
            nvr_channels
        )

        if not valid:
            QMessageBox.warning(
                self,
                "Save Profile",
                error
            )
            return

        profiles = get_profiles()

        if profile_id not in profiles:
            QMessageBox.critical(
                self,
                "Save Profile",
                "The profile no longer exists."
            )
            return

        profile_data = profiles[profile_id].copy()

        profile_data["name"] = profile_name
        profile_data["NVR_USER"] = nvr_user
        profile_data["NVR_IP"] = nvr_ip
        profile_data["NVR_PORT"] = nvr_port
        profile_data["TOTAL_CHANNELS"] = int(nvr_channels)

        if not update_profile(profile_id, profile_data):
            QMessageBox.critical(
                self,
                "Save Profile",
                "The profile could not be saved."
            )
            return

        if not set_nvr_password(profile_id, nvr_password):
            QMessageBox.critical(
                self,
                "Save Profile",
                "The profile data was saved, but the password could not "
                "be updated in the system keyring.\n\n"
                "The application will not restart. Check the keyring "
                "and verify the stored password before reconnecting."
            )
            return


        if profile_id == get_active_profile():
            QMessageBox.information(
                self,
                "Profile Updated",
                "The active profile was updated successfully.\n\n"
                "If you changed the connection parameters or password, "
                "make sure they also match the settings on the physical NVR.\n\n"
                "The application will now restart."
            )

            os.execv(sys.executable, [sys.executable] + sys.argv)

        else:
            QMessageBox.information(
                self,
                "Profile Updated",
                f"The profile '{profile_name}' was updated successfully.\n\n"
                "The changes have been saved and will take effect "
                "the next time you activate this profile.\n\n"
                "The application does not need to restart."
            )

            self.load_profiles()
            self.cancel_profile_edit()

    def cancel_profile_edit(self):
        """
        Cancela la edición y restaura el formulario de creación.
        """
        self.editing_profile_id = None
        self.editing_profile_name = None

        self.profile_name.clear()
        self.nvr_username.clear()
        self.nvr_password.clear()
        self.nvr_password_confirm.clear()
        self.nvr_ip.clear()
        self.nvr_port.clear()
        self.nvr_channels.clear()

        self.editing_profile_label.hide()
        self.create_profile_button.show()
        self.save_profile_button.hide()
        self.cancel_edit_button.hide()

    def delete_selected_profile(self):
        """
        Elimina el perfil seleccionado de la lista.
        """
        selected_item = self.profile_list.currentItem()

        if selected_item is None:
            QMessageBox.information(
                self,
                "Delete Profile",
                "Please select a profile to delete."
            )
            return

        profile_id = selected_item.data(Qt.ItemDataRole.UserRole)
        profile_name = selected_item.text()

        reply = QMessageBox.warning(
            self,
            "Delete Profile",
            f"Are you sure you want to delete the profile '{profile_name}'?",
            QMessageBox.StandardButton.Ok
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel
        )

        if reply != QMessageBox.StandardButton.Ok:
            return

        if not delete_profile(profile_id):
            QMessageBox.critical(
                self,
                "Delete Profile",
                "The profile could not be deleted.\n\n"
                "Make sure the selected profile is not the active profile."
            )
            return

        self.load_profiles()

        QMessageBox.information(
            self,
            "Delete Profile",
            "The profile was deleted successfully."
        )

    def create_new_profile(self):
        """
        Crea un nuevo perfil a partir de los datos ingresados
        en NVR Connection Configuration.
        """

        profile_name = self.profile_name.text().strip()
        nvr_user = self.nvr_username.text().strip()
        nvr_password = self.nvr_password.text()
        nvr_password_confirm = self.nvr_password_confirm.text()
        nvr_ip = self.nvr_ip.text().strip()
        nvr_port = self.nvr_port.text().strip()
        nvr_channels = self.nvr_channels.text().strip()

        if not nvr_password:
            print("Error al crear perfil: la contraseña es obligatoria")
            return
        if not nvr_password_confirm:
            print("Error al crear perfil: falta confirmar la contraseña")
            return
        if any(char.isspace() for char in nvr_password):
            print("Error al crear perfil: la contraseña no puede contener espacios")
            return
        if nvr_password != nvr_password_confirm:
            print("Error al crear perfil: las contraseñas no coinciden")
            return

        valid, error = validate_profile(
            profile_name,
            nvr_user,
            nvr_ip,
            nvr_port,
            nvr_channels
        )

        if not valid:
            print(f"Error al crear perfil: {error}")
            return

        profiles = get_profiles()

        profile_id = generate_profile_id(profile_name)

        if profile_id in profiles:
            print("Error al crear perfil: ese nombre ya existe")
            return

        profile_data = get_default_profile()

        profile_data["name"] = profile_name
        profile_data["NVR_USER"] = nvr_user
        profile_data["NVR_IP"] = nvr_ip
        profile_data["NVR_PORT"] = nvr_port
        profile_data["TOTAL_CHANNELS"] = int(nvr_channels)

        if not create_profile(profile_id, profile_data):
            print("Error al crear el perfil")
            return

        if nvr_password:
            set_nvr_password(profile_id, nvr_password)

        self.load_profiles()
        
        self.profile_name.clear()
        self.nvr_username.clear()
        self.nvr_password.clear()
        self.nvr_password_confirm.clear()
        self.nvr_ip.clear()
        self.nvr_port.clear()
        self.nvr_channels.clear()

        print(f"Perfil creado correctamente: {profile_name}")

    def activate_profile(self):
        """
        Activa el perfil seleccionado y reinicia la aplicación
        para aplicar la nueva configuración.
        """

        index = self.active_profile_combo.currentIndex()

        if index < 0:
            return

        profile_id = self.active_profile_combo.itemData(index)

        if not profile_id:
            return

        current_profile = get_active_profile()

        if profile_id == current_profile:
            return

        profile_name = self.active_profile_combo.currentText()

        reply = QMessageBox.question(
            self,
            "Change active profile",
            f"Changing the active profile to '{profile_name}' "
            "will restart the application.\n\n"
            "Do you want to continue?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        if not set_active_profile(profile_id):
            QMessageBox.critical(
                self,
                "Error",
                "The active profile could not be changed."
            )
            return

        os.execv(
            sys.executable,
            [sys.executable] + sys.argv
        )
