from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QLineEdit, QComboBox, QScrollArea, QListWidget

class ConfigurationTab(QWidget):
    def __init__(self):
        super().__init__()

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
        self.delete_config_layout = QHBoxLayout()
        self.delete_config_layout.addWidget(self.delete_config_label)
        self.delete_config_layout.addWidget(self.delete_config_button)
        self.delete_config_layout.addStretch()

        self.right_layout.addWidget(self.nvr_title)
        self.right_layout.addWidget(self.nvr_description)
        self.right_layout.addSpacing(8)

        self.right_layout.addWidget(self.separator_1)
        self.right_layout.addSpacing(8)

        self.right_layout.addLayout(self.configuration_file_layout)
        self.right_layout.addLayout(self.generate_config_layout)
        self.right_layout.addLayout(self.delete_config_layout)

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

        self.connection_fields = [
            ("Profile name:", "profile_name"),
            ("Username NVR:", "nvr_username"),
            ("Password NVR:", "nvr_password"),
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

            if field_name == "nvr_password":
                field.setEchoMode(QLineEdit.EchoMode.Password)

            setattr(self, field_name, field)

            row.addWidget(label)
            row.addWidget(field)
            row.addStretch()

            self.right_layout.addLayout(row)
        
        self.create_profile_button = QPushButton("Create")
        self.create_profile_button.setFixedWidth(100)
        self.create_profile_button.setStyleSheet(self.action_button_style)

        self.create_profile_layout = QHBoxLayout()
        self.create_profile_layout.setContentsMargins(0, 8, 0, 0)
        self.create_profile_layout.setSpacing(10)
        self.create_profile_layout.addSpacing(200)
        self.create_profile_layout.addWidget(self.create_profile_button)
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
        self.active_profile_combo.addItem("Casa")

        self.activate_profile_button = QPushButton("Activate")
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

        self.profile_list.addItem("Casa")
        self.profile_list.addItem("Trabajo")
        self.profile_list.addItem("Test")

        self.right_layout.addWidget(self.profile_list)

        self.profile_actions_layout = QHBoxLayout()
        self.profile_actions_layout.setContentsMargins(0, 8, 0, 0)
        self.profile_actions_layout.setSpacing(10)

        self.delete_profile_button = QPushButton("Delete")
        self.edit_profile_button = QPushButton("Edit")
        self.test_profile_button = QPushButton("Test")

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
