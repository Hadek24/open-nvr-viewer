"""
configuration_tab.py

Ventana de configuración general de Open NVR Viewer.

Responsabilidades:
- Construir el panel de navegación izquierdo.
- Construir el contenedor de contenido derecho.
- Integrar las secciones de configuración, actualmente NVRSection.

La lógica específica del NVR y la gestión de perfiles pertenecen
a configuration_tab_section/nvr.py.
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
)

from src.styles import (
    configuration_panel_style,
    configuration_menu_button_style,
    configuration_title_style,
)

from src.configuration_tab_section.nvr import NVRSection

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
        self.nvr_button = QPushButton("NVR")
        self.option1_button = QPushButton("RTSP")
        self.option2_button = QPushButton("TSHOOT")
        self.option3_button = QPushButton("CAMARAS")
        self.option4_button = QPushButton("UPGRADE")
        self.option5_button = QPushButton("LOGS")

        # Aplicar estilo común a los botones
        navigation_buttons = [
            self.nvr_button,
            self.option1_button,
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

        # Sección NVR
        self.nvr_section = NVRSection()
        self.right_panel_layout.addWidget(self.nvr_section)

        # =============================================================
        # 4. Integración de los paneles en el layout principal
        # =============================================================

        self.layout.addWidget(self.left_panel, 1)
        self.layout.addWidget(self.right_panel, 3)
