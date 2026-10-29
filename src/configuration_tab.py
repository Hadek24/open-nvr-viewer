"""
configuration_tab.py

Ventana de configuración general de Open NVR Viewer.

Responsabilidades:
- Construir el panel de navegación izquierdo.
- Construir el contenedor de contenido derecho.
- Integrar las secciones de configuración, Config File, Profiles y RTSP.

La gestión de las diferentes opciones están separadas en módulos propios.
"""

# ---------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
)

from src.styles import (
    configuration_panel_style,
    configuration_menu_button_style,
    configuration_title_style,
)

from src.configuration_tab_section.profiles import ProfilesSection
from src.configuration_tab_section.config_file import ConfigFileSection
from src.configuration_tab_section.rtsp import RTSPSection

# ---------------------------------------------------------------------
# ConfigurationTab
# ---------------------------------------------------------------------

class ConfigurationTab(QWidget):
    """
    Contenedor principal de la pestaña Configuration.

    Distribuye la interfaz en dos paneles:
    - Izquierdo: navegación entre secciones.
    - Derecho: contenido de la sección seleccionada.
    """

    def __init__(self):
        super().__init__()

        # =============================================================
        # 1. Layout principal
        # =============================================================

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(6, 6, 6, 6)
        self.layout.setSpacing(6)

        # =============================================================
        # 2. Panel izquierdo: navegación
        # =============================================================

        self.left_panel = QWidget()
        self.left_panel.setObjectName("configuration_left")
        self.left_panel.setStyleSheet(configuration_panel_style)
        self.left_layout = QVBoxLayout(self.left_panel)

        # Título del panel
        self.configuration_title = QLabel("Configuration")
        self.configuration_title.setStyleSheet(
            configuration_title_style
        )

        # Botones de navegación
        self.config_file_button = QPushButton("Config File")
        self.profiles_button = QPushButton("Profiles")
        self.rtsp_button = QPushButton("RTSP")
        self.option2_button = QPushButton("TSHOOT")
        self.option3_button = QPushButton("CAMARAS")
        self.option4_button = QPushButton("UPGRADE")
        self.option5_button = QPushButton("LOGS")

        # Aplicar estilo común a los botones
        navigation_buttons = [
            self.config_file_button,
            self.profiles_button,
            self.rtsp_button,
            self.option2_button,
            self.option3_button,
            self.option4_button,
            self.option5_button,
        ]

        for button in navigation_buttons:
            button.setStyleSheet(configuration_menu_button_style)

        # Distribución vertical del panel izquierdo
        self.left_layout.addWidget(self.configuration_title)

        for button in navigation_buttons:
            self.left_layout.addWidget(button)

        self.left_layout.addStretch()

        # =============================================================
        # 3. Panel derecho: contenido
        # =============================================================

        self.right_panel = QWidget()
        self.right_panel.setObjectName("configuration_right")

        self.right_panel_layout = QVBoxLayout(self.right_panel)
        self.right_panel_layout.setContentsMargins(0, 0, 0, 0)

        # Contenedor de secciones: cada botón muestra su propio panel.
        self.sections_stack = QStackedWidget()
        self.config_file_section = ConfigFileSection()
        self.profiles_section = ProfilesSection()
        self.rtsp_section = RTSPSection()
        self.sections_stack.addWidget(self.config_file_section)
        self.sections_stack.addWidget(self.profiles_section)
        self.sections_stack.addWidget(self.rtsp_section)

        # El panel derecho contiene únicamente el contenedor de secciones.
        self.right_panel_layout.addWidget(self.sections_stack)

        # Config File se muestra por defecto.
        self.sections_stack.setCurrentWidget(
            self.config_file_section
        )

        # Navegación entre las secciones implementadas.
        self.config_file_button.clicked.connect(
            lambda: self.sections_stack.setCurrentWidget(self.config_file_section)
        )

        self.profiles_button.clicked.connect(self.show_profiles_section)
        self.rtsp_button.clicked.connect(
            lambda: self.sections_stack.setCurrentWidget(self.rtsp_section)
        )
        self.rtsp_section.templates_changed.connect(
            self.profiles_section.load_rtsp_templates
        )

        # =============================================================
        # 4. Integración de los paneles en el layout principal
        # =============================================================

        self.layout.addWidget(self.left_panel, 1)
        self.layout.addWidget(self.right_panel, 3)

    def show_profiles_section(self):
        """Refresh RTSP choices before displaying the profile editor."""
        self.profiles_section.load_rtsp_templates()
        self.sections_stack.setCurrentWidget(self.profiles_section)
