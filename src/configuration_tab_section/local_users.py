
"""
local_users.py

Local user management interface for Open NVR Viewer.

This initial version provides the graphical interface only.
User information is kept in memory and is not persisted.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QDialog,
    QFormLayout,
    QDialogButtonBox,
    QMessageBox,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QHeaderView,
)
from PyQt6.QtCore import Qt
from src.config import get_profiles
from src.user_manager import UserManager
from src.styles import (
    configuration_action_button_style,
    configuration_scroll_area_style,
    configuration_section_title_style,
    configuration_section_description_style,
    configuration_subsection_title_style,
    configuration_separator_style,
    rtsp_template_table_style,
    local_user_field_style,
    local_user_combo_style,
)

class UserDetailsDialog(QDialog):
    """Dialog for adding or editing a local user."""

    def __init__(self, user=None, parent=None):
        super().__init__(parent)

        self.user = user or {}

        self.setWindowTitle(
            "Edit User" if user else "Add User"
        )
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Username
        self.username_field = QLineEdit()
        self.username_field.setStyleSheet(
            local_user_field_style
        )
        self.username_field.setPlaceholderText("Enter username")

        if user:
            self.username_field.setText(user["username"])

        form_layout.addRow("Username:", self.username_field)

        # Password
        self.password_field = QLineEdit()
        self.password_field.setEchoMode(
            QLineEdit.EchoMode.Password
        )
        self.password_field.setStyleSheet(
            local_user_field_style
        )
        self.password_field.setPlaceholderText(
            "Leave empty to keep current password"
            if user else "Enter password"
        )

        form_layout.addRow("Password:", self.password_field)

        # Confirm password
        self.confirm_password_field = QLineEdit()
        self.confirm_password_field.setEchoMode(
            QLineEdit.EchoMode.Password
        )
        self.confirm_password_field.setStyleSheet(
            local_user_field_style
        )
        self.confirm_password_field.setPlaceholderText(
            "Confirm password"
        )

        form_layout.addRow(
            "Confirm Password:",
            self.confirm_password_field
        )

        # Role
        self.role_combo = QComboBox()
        self.role_combo.setStyleSheet(
            local_user_combo_style
        )
        self.role_combo.addItems([
            "Administrator",
            "Viewer",
        ])

        if user:
            self.role_combo.setCurrentText(user["role"])

        form_layout.addRow("Role:", self.role_combo)

        # Assigned Profile
        self.profile_combo = QComboBox()
        self.profile_combo.setStyleSheet(
            local_user_combo_style
        )

        profiles = get_profiles()

        for profile_id, profile_data in profiles.items():
            profile_name = profile_data.get(
                "name",
                profile_id
            )
            self.profile_combo.addItem(
                profile_name,
                profile_id
            )

        if user:
            assigned_profile = user.get(
                "assigned_profile",
                user.get("profile")
            )

            profile_index = self.profile_combo.findData(
                assigned_profile
            )

            if profile_index >= 0:
                self.profile_combo.setCurrentIndex(
                    profile_index
                )

        form_layout.addRow(
            "Assigned Profile:",
            self.profile_combo
        )

        # Disabled status
        self.disabled_checkbox = QCheckBox("Disabled")

        if user:
            self.disabled_checkbox.setChecked(
                user["disabled"]
            )

        form_layout.addRow(
            "Account Status:",
            self.disabled_checkbox
        )

        layout.addLayout(form_layout)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def validate_and_accept(self):
        """Validate the form before accepting it."""

        username = self.username_field.text().strip()
        password = self.password_field.text()
        confirm_password = self.confirm_password_field.text()

        if not username:
            QMessageBox.warning(
                self,
                "Invalid User",
                "Username is required."
            )
            return

        if not self.user and not password:
            QMessageBox.warning(
                self,
                "Invalid Password",
                "Password is required."
            )
            return

        if password and len(password) < 8:
            QMessageBox.warning(
                self,
                "Invalid Password",
                "Password must contain at least 8 characters."
            )
            return

        if password or confirm_password:
            if password != confirm_password:
                QMessageBox.warning(
                    self,
                    "Password Mismatch",
                    "Passwords do not match."
                )
                return

        self.accept()

    def get_user_data(self):
        """Return the information entered in the form."""

        return {
            "username": self.username_field.text().strip(),
            "role": self.role_combo.currentText(),
            "profile": self.profile_combo.currentData(),
            "disabled": self.disabled_checkbox.isChecked(),
        }

    def get_password(self):
        """Return the password entered in the form."""
        return self.password_field.text()

class LocalUsersSection(QWidget):
    """Graphical interface for managing local users."""

    def __init__(self, actor_id, parent=None):
        super().__init__(parent)

        # User manager
        self.actor_id = actor_id
        self.user_manager = UserManager()
        self.users = []

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Right-side framed container, matching RTSPSection.
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(
            QScrollArea.Shape.StyledPanel
        )
        self.scroll_area.setStyleSheet(
            configuration_scroll_area_style
        )

        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(
            20, 20, 20, 20
        )
        self.content_layout.setSpacing(10)

        self.scroll_area.setWidget(self.content)
        self.main_layout.addWidget(self.scroll_area)

        # Section title
        self.title = QLabel("Local Users")
        self.title.setStyleSheet(
            configuration_section_title_style
        )

        self.description = QLabel(
            "Manage local application users, their roles, "
            "assigned NVR profiles and account status."
        )
        self.description.setWordWrap(True)
        self.description.setStyleSheet(
            configuration_section_description_style
        )

        self.content_layout.addWidget(self.title)
        self.content_layout.addWidget(self.description)

        # Separator
        separator = QLabel()
        separator.setFixedHeight(1)
        separator.setStyleSheet(
            configuration_separator_style
        )

        self.content_layout.addSpacing(8)
        self.content_layout.addWidget(separator)
        self.content_layout.addSpacing(8)

        # Users table title
        self.users_title = QLabel("Configured Users")
        self.users_title.setStyleSheet(
            configuration_subsection_title_style
        )

        self.content_layout.addWidget(self.users_title)

        # Add spacing between title and table.
        self.content_layout.addSpacing(6)

        # Users table
        self.users_table = QTableWidget(0, 4)
        self.users_table.setHorizontalHeaderLabels([
            "Username",
            "Role",
            "Assigned Profile",
            "Status",
        ])

        self.users_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.users_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.users_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.users_table.verticalHeader().setVisible(False)

        self.users_table.setStyleSheet(
            rtsp_template_table_style
        )

        header = self.users_table.horizontalHeader()

        # Keep the first, second and fourth columns at
        # reasonable widths. The profile column uses the
        # remaining space instead of dominating the table.
        header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.Interactive
        )
        header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.Interactive
        )
        header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        header.setSectionResizeMode(
            3, QHeaderView.ResizeMode.Interactive
        )

        self.users_table.setColumnWidth(0, 150)
        self.users_table.setColumnWidth(1, 130)
        self.users_table.setColumnWidth(3, 110)

        self.users_table.setMinimumHeight(180)

        self.content_layout.addWidget(self.users_table)

        # Action buttons
        self.actions_layout = QHBoxLayout()

        self.add_button = QPushButton("Add User")
        self.edit_button = QPushButton("Edit User")
        self.delete_button = QPushButton("Delete User")

        for button in (
            self.add_button,
            self.edit_button,
            self.delete_button,
        ):
            button.setStyleSheet(
                configuration_action_button_style
            )
            button.setFixedWidth(110)
            self.actions_layout.addWidget(button)

        self.actions_layout.addStretch()
        self.content_layout.addLayout(self.actions_layout)

        # Button connections
        self.add_button.clicked.connect(self.add_user)
        self.edit_button.clicked.connect(self.edit_user)
        self.delete_button.clicked.connect(self.delete_user)

        self.load_users_from_manager()
        self.content_layout.addStretch()

    def refresh_users_table(self):
        """Refresh the users table using the current in-memory data."""

        self.users_table.setRowCount(0)

        for user in self.users:
            row = self.users_table.rowCount()
            self.users_table.insertRow(row)

            status = (
                "Disabled"
                if user["disabled"]
                else "Active"
            )

            values = [
                user["username"],
                user["role"],
                user["profile"],
                status,
            ]

            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignVCenter
                    | Qt.AlignmentFlag.AlignLeft
                )
                self.users_table.setItem(
                    row,
                    column,
                    item
                )

    def load_users_from_manager(self):
        """Load users from the persistent user manager."""

        try:
            stored_users = self.user_manager.list_users()
            profiles = get_profiles()

            self.users = []

            for user in stored_users:
                assigned_profile = user["assigned_profile"]

                profile_data = profiles.get(assigned_profile, {}) if assigned_profile else {}
                profile_name = profile_data.get("name", assigned_profile or "—")

                self.users.append({
                    "id": user["id"],
                    "username": user["username"],
                    "role": user["role"],
                    "profile": profile_name,
                    "assigned_profile": assigned_profile,
                    "disabled": not user["enabled"],
                })

        except (OSError, ValueError) as error:
            QMessageBox.critical(
                self,
                "User Loading Error",
                f"Could not load local users:\n{error}"
            )

        self.refresh_users_table()

    def get_selected_user_index(self):
        """Return the selected user's index."""

        row = self.users_table.currentRow()

        if row < 0:
            QMessageBox.information(
                self,
                "Select User",
                "Please select a user first."
            )
            return None

        return row

    def add_user(self):
        """Open the dialog to add a user."""

        if not get_profiles():
            QMessageBox.information(
                self,
                "NVR profile required",
                "Create an NVR profile before adding local users.",
            )
            return

        dialog = UserDetailsDialog(parent=self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            user = dialog.get_user_data()
            password = dialog.get_password()

            try:
                self.user_manager.add_user(
                    actor_id=self.actor_id,
                    username=user["username"],
                    password=password,
                    role=user["role"],
                    assigned_profile=user["profile"],
                    enabled=not user["disabled"],
                )

                self.load_users_from_manager()

            except (ValueError, PermissionError) as error:
                QMessageBox.warning(
                    self,
                    "User Creation Error",
                    str(error)
                )

            except OSError as error:
                QMessageBox.critical(
                    self,
                    "User Storage Error",
                    f"Could not save the user:\n{error}"
                )

    def edit_user(self):
        """Open the dialog to edit the selected user."""

        index = self.get_selected_user_index()

        if index is None:
            return

        current_user = self.users[index]

        dialog = UserDetailsDialog(
            user=current_user,
            parent=self
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_user = dialog.get_user_data()
            password = dialog.get_password()

            try:
                self.user_manager.edit_user(
                    actor_id=self.actor_id,
                    username=current_user["username"],
                    new_username=updated_user["username"],
                    password=password,
                    role=updated_user["role"],
                    assigned_profile=updated_user["profile"],
                    enabled=not updated_user["disabled"],
                )

                self.load_users_from_manager()

            except (ValueError, PermissionError) as error:
                QMessageBox.warning(
                    self,
                    "User Update Error",
                    str(error)
                )

            except OSError as error:
                QMessageBox.critical(
                    self,
                    "User Storage Error",
                    f"Could not update the user:\n{error}"
                )

    def delete_user(self):
        """Delete the selected user from persistent storage."""

        index = self.get_selected_user_index()

        if index is None:
            return

        username = self.users[index]["username"]

        confirmation = QMessageBox.question(
            self,
            "Delete User",
            f"Are you sure you want to delete '{username}'?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirmation == QMessageBox.StandardButton.Yes:
            try:
                self.user_manager.delete_user(self.actor_id, username)
                self.load_users_from_manager()

            except (ValueError, PermissionError) as error:
                QMessageBox.warning(
                    self,
                    "User Deletion Error",
                    str(error)
                )

            except OSError as error:
                QMessageBox.critical(
                    self,
                    "User Storage Error",
                    f"Could not delete the user:\n{error}"
                )
