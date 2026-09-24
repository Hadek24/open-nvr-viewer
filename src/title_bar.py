from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtWidgets import QWidget, QGridLayout, QLabel, QHBoxLayout, QPushButton

class TitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.parent_window = parent
        self.drag_position = QPoint()

        self.setFixedHeight(34)
        self.setObjectName("title_bar")

        layout = QGridLayout(self)
        layout.setContentsMargins(10, 0, 4, 0)
        layout.setHorizontalSpacing(4)

        # Columnas laterales con el mismo peso para centrar
        # el título respecto de toda la ventana.
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(2, 1)

        self.title_label = QLabel("Open NVR Viewer")
        self.title_label.setObjectName("title_label")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # El texto no intercepta los eventos del mouse.
        self.title_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        layout.addWidget(self.title_label, 0, 1, alignment=Qt.AlignmentFlag.AlignCenter)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(4)

        self.minimize_button = QPushButton("−")
        self.maximize_button = QPushButton("□")
        self.close_button = QPushButton("×")

        self.minimize_button.setObjectName("title_button")
        self.maximize_button.setObjectName("title_button")
        self.close_button.setObjectName("close_button")

        self.minimize_button.clicked.connect(self.parent_window.showMinimized)
        self.maximize_button.clicked.connect(self.toggle_maximize)
        self.close_button.clicked.connect(self.parent_window.close)

        for button in (
            self.minimize_button,
            self.maximize_button,
            self.close_button
        ):
            button.setFixedSize(32, 28)
            buttons_layout.addWidget(button)

        layout.addLayout(
            buttons_layout,
            0,
            2,
            alignment=Qt.AlignmentFlag.AlignRight
        )

    def toggle_maximize(self):
        if self.parent_window.isMaximized():
            self.parent_window.showNormal()
            self.maximize_button.setText("□")
        else:
            self.parent_window.showMaximized()
            self.maximize_button.setText("❐")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = (
                event.globalPosition().toPoint()
                - self.parent_window.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        if (
            event.buttons() & Qt.MouseButton.LeftButton
            and not self.parent_window.isMaximized()
        ):
            self.parent_window.move(
                event.globalPosition().toPoint()
                - self.drag_position
            )
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_maximize()
            event.accept()
