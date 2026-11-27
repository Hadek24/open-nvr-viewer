from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFormLayout,
)


class InitialSuperadminDialog(QDialog):
    """First-run/bootstrap dialog for the installation Superadmin."""

    def __init__(self, existing_users=False, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Open NVR Viewer - Initial Setup")
        self.setMinimumWidth(430)
        self.setModal(True)
        layout = QVBoxLayout(self)

        title = QLabel("Initial administrator setup")
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        layout.addWidget(title)

        if existing_users:
            message = (
                "This installation already contains local accounts, but no Superadmin. "
                "Create the Superadmin account now. Existing users and passwords will be preserved."
            )
        else:
            message = (
                "Create the first local account. It will be the installation Superadmin."
            )
        description = QLabel(message)
        description.setWordWrap(True)
        layout.addWidget(description)

        form = QFormLayout()
        self.username = QLineEdit()
        self.username.setPlaceholderText("Superadmin username")
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setPlaceholderText("At least 8 characters")
        self.confirm = QLineEdit()
        self.confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm.setPlaceholderText("Repeat password")
        form.addRow("Username:", self.username)
        form.addRow("Password:", self.password)
        form.addRow("Confirm password:", self.confirm)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        self.create_button = QPushButton("Create Superadmin")
        self.cancel_button = QPushButton("Exit")
        self.create_button.clicked.connect(self._validate)
        self.cancel_button.clicked.connect(self.reject)
        buttons.addStretch()
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.create_button)
        layout.addLayout(buttons)

    def _validate(self):
        username = self.username.text().strip()
        password = self.password.text()
        confirm = self.confirm.text()
        if not username:
            QMessageBox.warning(self, "Invalid username", "Username is required.")
            return
        if len(password) < 8:
            QMessageBox.warning(self, "Invalid password", "Password must contain at least 8 characters.")
            return
        if password != confirm:
            QMessageBox.warning(self, "Password mismatch", "Passwords do not match.")
            return
        self.accept()

    def get_credentials(self):
        return self.username.text().strip(), self.password.text()


class LoginDialog(QDialog):
    """Local application login dialog."""

    def __init__(self, user_manager, parent=None):
        super().__init__(parent)
        self.user_manager = user_manager
        self.session_user = None
        self.setWindowTitle("Open NVR Viewer - Login")
        self.setMinimumWidth(390)
        self.setModal(True)
        layout = QVBoxLayout(self)

        title = QLabel("Open NVR Viewer")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: 600; padding: 12px;")
        layout.addWidget(title)

        form = QFormLayout()
        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setPlaceholderText("Password")
        self.password.returnPressed.connect(self._login)
        form.addRow("Username:", self.username)
        form.addRow("Password:", self.password)
        layout.addLayout(form)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #F85149;")
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)

        buttons = QHBoxLayout()
        self.login_button = QPushButton("Login")
        self.cancel_button = QPushButton("Exit")
        self.login_button.clicked.connect(self._login)
        self.cancel_button.clicked.connect(self.reject)
        buttons.addStretch()
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.login_button)
        layout.addLayout(buttons)

    def _login(self):
        try:
            session = self.user_manager.authenticate(
                self.username.text(), self.password.text()
            )
        except (OSError, ValueError) as error:
            self.error_label.setText(f"Could not validate local accounts: {error}")
            return

        if session is None:
            self.password.clear()
            self.error_label.setText("Invalid username/password or account disabled.")
            return

        self.session_user = session
        self.accept()
