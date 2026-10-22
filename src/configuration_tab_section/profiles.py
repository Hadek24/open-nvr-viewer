
"""
nvr.py

Gestión de perfiles de conexión NVR para Open NVR Viewer.

Responsabilidades:
- Crear, editar, activar y eliminar perfiles de conexión.
- Ejecutar pruebas de conectividad mediante ConnectionTestThread.
- Mostrar los resultados de diagnóstico mediante ConnectionTestDialog.
"""

# ---------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------

# Standard library
import os
import sys

# PyQt6
from PyQt6.QtCore import Qt

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QScrollArea,
    QListWidget,
    QMessageBox,
    QInputDialog,
    QDialog,
    QGridLayout,
)

# Application configuration and profile management
from src.config import (
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
)

# Connection diagnostics
from src.configuration_tab_section.connection_test import ConnectionTestThread

# Import styles
from src.styles import (
    configuration_action_button_style,
    configuration_editing_label_style,
    configuration_field_style,
    configuration_scroll_area_style,
    configuration_section_title_style,
    configuration_section_description_style,
    configuration_subsection_title_style,
    configuration_field_label_style,
    configuration_separator_style,
    configuration_profile_list_style,
    connection_test_title_style,
    connection_test_pending_style,
    connection_test_success_style,
    connection_test_failure_style,
)

# ---------------------------------------------------------------------
# ConnectionTestDialog
# ---------------------------------------------------------------------

class ConnectionTestDialog(QDialog):
    """
    Dialog displaying the results of NVR connection diagnostics.

    Shows the status of each test and updates the result labels
    as diagnostic information becomes available.
    """

    def __init__(self, profile_name, parent=None):
        """Initialize the diagnostic dialog and its result indicators."""
        super().__init__(parent)

        self.setWindowTitle("NVR Connection Test")
        self.setMinimumWidth(480)

        # Main layout
        layout = QVBoxLayout(self)

        # Dialog title
        title = QLabel(f"Connection diagnostics: {profile_name}")
        title.setStyleSheet(connection_test_title_style)
        layout.addWidget(title)

        # Result indicators, indexed by test key
        self.results = {}

        tests = [
            ("ping", "Ping"),
            ("port", "RTSP TCP Port"),
            ("credentials", "RTSP Credentials"),
            ("rtsp", "RTSP Connection"),
            ("frame", "Video Frame Received"),
        ]

        # Test result grid
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)

        for row, (key, label_text) in enumerate(tests):
            label = QLabel(label_text)
            status = QLabel("Pending")
            status.setStyleSheet(connection_test_pending_style)

            grid.addWidget(label, row, 0)
            grid.addWidget(status, row, 1)

            self.results[key] = status

        layout.addLayout(grid)

        # Close button
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        layout.addWidget(self.close_button)

    def update_result(self, key, success, message):
        """Update the status indicator for a completed connection test."""
        status = self.results[key]

        if success:
            status.setText(f"✓ OK — {message}")
            status.setStyleSheet(connection_test_success_style)
        else:
            status.setText(f"✗ Failed — {message}")
            status.setStyleSheet(connection_test_failure_style)

class ProfilesSection(QWidget):
    """Manage NVR connection profiles and diagnostics."""

    def __init__(self, parent=None):
        """Initialize the NVR configuration interface."""
        super().__init__(parent)

        # -------------------------------------------------------------
        # Profile editing state
        # -------------------------------------------------------------

        self.editing_profile_id = None
        self.editing_profile_name = None

        # -------------------------------------------------------------
        # Main layout and scroll area
        # -------------------------------------------------------------

        self.right_panel_layout = QVBoxLayout(self)
        self.right_panel_layout.setContentsMargins(0, 0, 0, 0)

        self.right_scroll = QScrollArea()
        self.right_scroll.setWidgetResizable(True)
        self.right_scroll.setFrameShape(QScrollArea.Shape.StyledPanel)
        self.right_scroll.setStyleSheet(configuration_scroll_area_style)

        self.right_content = QWidget()
        self.right_layout = QVBoxLayout(self.right_content)
        self.right_layout.setContentsMargins(20, 20, 20, 20)
        self.right_layout.setSpacing(10)

        self.right_scroll.setWidget(self.right_content)
        self.right_panel_layout.addWidget(self.right_scroll)

        # -------------------------------------------------------------
        # Profiles section: title and description
        # -------------------------------------------------------------

        self.nvr_title = QLabel("Profiles")
        self.nvr_title.setStyleSheet(configuration_section_title_style)

        self.nvr_description = QLabel(
            "Create and manage connection profiles for your NVR devices. "
            "Each profile stores its own connection settings."
        )
        self.nvr_description.setWordWrap(True)
        self.nvr_description.setStyleSheet(configuration_section_description_style)

        self.right_layout.addWidget(self.nvr_title)
        self.right_layout.addWidget(self.nvr_description)

        # -------------------------------------------------------------
        # NVR connection configuration
        # -------------------------------------------------------------

        self.separator_2 = QLabel()
        self.separator_2.setFixedHeight(1)
        self.separator_2.setStyleSheet(configuration_separator_style)

        self.connection_title = QLabel("NVR Connection Configuration")
        self.connection_title.setStyleSheet(configuration_subsection_title_style)

        self.right_layout.addSpacing(8)
        self.right_layout.addWidget(self.separator_2)
        self.right_layout.addSpacing(8)
        self.right_layout.addWidget(self.connection_title)

        # Profile editing indicator
        self.editing_profile_label = QLabel("")
        self.editing_profile_label.setStyleSheet(configuration_editing_label_style)
        self.editing_profile_label.hide()

        self.right_layout.addWidget(self.editing_profile_label)

        # Connection fields
        self.connection_fields = [
            ("Profile name:", "profile_name"),
            ("Username NVR:", "nvr_username"),
            ("Password NVR:", "nvr_password"),
            ("Confirm password:", "nvr_password_confirm"),
            ("NVR IP:", "nvr_ip"),
            ("NVR Port:", "nvr_port"),
            ("NVR channels:", "nvr_channels"),
        ]

        for label_text, field_name in self.connection_fields:
            row = QHBoxLayout()

            label = QLabel(label_text)
            label.setFixedWidth(190)
            label.setStyleSheet(configuration_field_label_style)

            field = QLineEdit()
            field.setFixedWidth(250)
            field.setStyleSheet(configuration_field_style)

            if field_name in ("nvr_password", "nvr_password_confirm"):
                field.setEchoMode(QLineEdit.EchoMode.Password)

            setattr(self, field_name, field)

            row.addWidget(label)
            row.addWidget(field)
            row.addStretch()

            self.right_layout.addLayout(row)

        # Profile creation and editing buttons
        self.create_profile_button = QPushButton("Create")
        self.create_profile_button.clicked.connect(self.create_new_profile)
        self.create_profile_button.setFixedWidth(100)
        self.create_profile_button.setStyleSheet(configuration_action_button_style)

        self.save_profile_button = QPushButton("Save Changes")
        self.save_profile_button.clicked.connect(self.save_edited_profile)
        self.save_profile_button.setFixedWidth(120)
        self.save_profile_button.setStyleSheet(configuration_action_button_style)
        self.save_profile_button.hide()

        self.cancel_edit_button = QPushButton("Cancel")
        self.cancel_edit_button.clicked.connect(self.cancel_profile_edit)
        self.cancel_edit_button.setFixedWidth(100)
        self.cancel_edit_button.setStyleSheet(configuration_action_button_style)
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

        # -------------------------------------------------------------
        # Connection profile management
        # -------------------------------------------------------------

        self.separator_3 = QLabel()
        self.separator_3.setFixedHeight(1)
        self.separator_3.setStyleSheet(configuration_separator_style)

        self.profile_management_title = QLabel("Manage Connection Profiles")
        self.profile_management_title.setStyleSheet(configuration_subsection_title_style)

        self.right_layout.addSpacing(12)
        self.right_layout.addWidget(self.separator_3)
        self.right_layout.addSpacing(8)
        self.right_layout.addWidget(self.profile_management_title)

        # Active profile selector
        self.active_profile_layout = QHBoxLayout()

        self.active_profile_label = QLabel("Active Profile:")
        self.active_profile_label.setFixedWidth(190)
        self.active_profile_label.setStyleSheet(configuration_field_label_style)

        self.active_profile_combo = QComboBox()
        self.active_profile_combo.setFixedWidth(250)

        self.activate_profile_button = QPushButton("Activate")
        self.activate_profile_button.clicked.connect(self.activate_profile)
        self.activate_profile_button.setFixedWidth(100)
        self.activate_profile_button.setStyleSheet(configuration_action_button_style)

        self.active_profile_layout.addWidget(self.active_profile_label)
        self.active_profile_layout.addWidget(self.active_profile_combo)
        self.active_profile_layout.addSpacing(10)
        self.active_profile_layout.addWidget(self.activate_profile_button)
        self.active_profile_layout.addStretch()

        self.right_layout.addLayout(self.active_profile_layout)

        # Profile list
        self.profile_list_title = QLabel("Profile Management")
        self.profile_list_title.setStyleSheet(configuration_subsection_title_style)

        self.right_layout.addSpacing(10)
        self.right_layout.addWidget(self.profile_list_title)

        self.profile_list = QListWidget()
        self.profile_list.setFixedWidth(320)
        self.profile_list.setMinimumHeight(120)
        self.profile_list.setStyleSheet(configuration_profile_list_style)

        self.right_layout.addWidget(self.profile_list)

        # Profile actions
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

        self.delete_profile_button.setStyleSheet(configuration_action_button_style)
        self.edit_profile_button.setStyleSheet(configuration_action_button_style)
        self.test_profile_button.setStyleSheet(configuration_action_button_style)

        self.profile_actions_layout.addWidget(self.delete_profile_button)
        self.profile_actions_layout.addWidget(self.edit_profile_button)
        self.profile_actions_layout.addWidget(self.test_profile_button)
        self.profile_actions_layout.addStretch()

        self.right_layout.addLayout(self.profile_actions_layout)

        # Load existing connection profiles.
        self.load_profiles()

    # -----------------------------------------------------------------
    # Connection profile loading
    # -----------------------------------------------------------------

    def load_profiles(self):
        """Load available profiles into the profile selection controls."""
        profiles = get_profiles()
        active_profile = get_active_profile()

        self.active_profile_combo.clear()
        self.profile_list.clear()

        for profile_id, profile in profiles.items():
            profile_name = profile.get("name", profile_id)

            self.active_profile_combo.addItem(
                profile_name,
                profile_id,
            )

            self.profile_list.addItem(profile_name)
            item = self.profile_list.item(
                self.profile_list.count() - 1
            )
            item.setData(Qt.ItemDataRole.UserRole, profile_id)

        # Select the active profile when it exists in the combo box.
        if active_profile:
            index = self.active_profile_combo.findData(active_profile)

            if index >= 0:
                self.active_profile_combo.setCurrentIndex(index)

    # -----------------------------------------------------------------
    # Edit connection profiles
    # -----------------------------------------------------------------

    def edit_selected_profile(self):
        """Verify the current password and load the selected profile for editing."""
        selected_item = self.profile_list.currentItem()

        if selected_item is None:
            QMessageBox.information(
                self,
                "Edit Profile",
                "Please select a profile to edit.",
            )
            return

        profile_id = selected_item.data(Qt.ItemDataRole.UserRole)
        profile_name = selected_item.text()

        # Verify the password stored in the system keyring.
        current_password = get_nvr_password(profile_id)

        if not current_password:
            QMessageBox.warning(
                self,
                "Edit Profile",
                "No password is stored for this profile. "
                "The profile cannot be edited.",
            )
            return

        password, accepted = QInputDialog.getText(
            self,
            "Verify Password",
            f"Enter the current NVR password for '{profile_name}':",
            QLineEdit.EchoMode.Password,
        )

        if not accepted:
            return

        if password != current_password:
            QMessageBox.warning(
                self,
                "Edit Profile",
                "The password is incorrect.",
            )
            return

        # Retrieve the selected profile configuration.
        profiles = get_profiles()
        profile_data = profiles.get(profile_id)

        if profile_data is None:
            QMessageBox.critical(
                self,
                "Edit Profile",
                "The selected profile could not be found.",
            )
            return

        # Store the profile currently being edited.
        self.editing_profile_id = profile_id
        self.editing_profile_name = profile_name

        # Populate the form with the existing profile data.
        self.profile_name.setText(profile_data.get("name", ""))
        self.nvr_username.setText(profile_data.get("NVR_USER", ""))
        self.nvr_password.setText(current_password)
        self.nvr_password_confirm.setText(current_password)
        self.nvr_ip.setText(profile_data.get("NVR_IP", ""))
        self.nvr_port.setText(str(profile_data.get("NVR_PORT", "")))
        self.nvr_channels.setText(str(profile_data.get("TOTAL_CHANNELS", "")))

        # Switch the form to editing mode.
        self.editing_profile_label.setText(f"Editing profile: {profile_name}")
        self.editing_profile_label.show()

        self.create_profile_button.hide()
        self.save_profile_button.show()
        self.cancel_edit_button.show()

        self.right_scroll.ensureWidgetVisible(self.editing_profile_label)

    # -----------------------------------------------------------------
    # Test connection profiles
    # -----------------------------------------------------------------

    def test_selected_profile(self):
        """Run connection diagnostics for the selected profile."""
        selected_item = self.profile_list.currentItem()

        if selected_item is None:
            QMessageBox.information(
                self,
                "Test Profile",
                "Please select a profile to test.",
            )
            return

        profile_id = selected_item.data(Qt.ItemDataRole.UserRole)

        profiles = get_profiles()
        profile_data = profiles.get(profile_id)

        if profile_data is None:
            QMessageBox.warning(
                self,
                "Test Profile",
                "The selected profile could not be found.",
            )
            return

        password = get_nvr_password(profile_id)

        if password is None:
            QMessageBox.warning(
                self,
                "Test Profile",
                "No password is stored for this profile.",
            )
            return

        profile_name = profile_data.get("name", profile_id)

        # Display the diagnostic results dialog.
        self.test_dialog = ConnectionTestDialog(
            profile_name,
            self,
        )
        self.test_dialog.show()

        # Start the connection test in a separate thread.
        self.test_thread = ConnectionTestThread(
            profile_data.get("NVR_IP", ""),
            profile_data.get("NVR_PORT", 0),
        )

        self.test_thread.result_ready.connect(self.show_connection_test_result)
        self.test_thread.start()

    def show_connection_test_result(
        self,
        test_name,
        success,
        message,):
        """Forward supported diagnostic results to the test dialog."""
        test_keys = {
            "Ping": "ping",
            "Puerto TCP": "port",
        }

        key = test_keys.get(test_name)

        if key and hasattr(self, "test_dialog"):
            self.test_dialog.update_result(
                key,
                success,
                message,
            )

    # -----------------------------------------------------------------
    # Save profile changes
    # -----------------------------------------------------------------

    def save_edited_profile(self):
        """Validate and save changes to the profile currently being edited."""
        profile_id = self.editing_profile_id

        if not profile_id:
            QMessageBox.warning(
                self,
                "Save Profile",
                "No profile is currently being edited.",
            )
            return

        # Read the values entered in the form.
        profile_name = self.profile_name.text().strip()
        nvr_user = self.nvr_username.text().strip()
        nvr_password = self.nvr_password.text()
        nvr_password_confirm = self.nvr_password_confirm.text()
        nvr_ip = self.nvr_ip.text().strip()
        nvr_port = self.nvr_port.text().strip()
        nvr_channels = self.nvr_channels.text().strip()

        # Validate password fields.
        if not nvr_password:
            QMessageBox.warning(
                self,
                "Save Profile",
                "The NVR password is required.",
            )
            return

        if not nvr_password_confirm:
            QMessageBox.warning(
                self,
                "Save Profile",
                "Please confirm the NVR password.",
            )
            return

        if any(char.isspace() for char in nvr_password):
            QMessageBox.warning(
                self,
                "Save Profile",
                "The password cannot contain spaces.",
            )
            return

        if nvr_password != nvr_password_confirm:
            QMessageBox.warning(
                self,
                "Save Profile",
                "The passwords do not match.",
            )
            return

        # Validate the remaining profile fields.
        valid, error = validate_profile(
            profile_name,
            nvr_user,
            nvr_ip,
            nvr_port,
            nvr_channels,
        )

        if not valid:
            QMessageBox.warning(
                self,
                "Save Profile",
                error,
            )
            return

        # Ensure the profile still exists before updating it.
        profiles = get_profiles()

        if profile_id not in profiles:
            QMessageBox.critical(
                self,
                "Save Profile",
                "The profile no longer exists.",
            )
            return

        # Preserve existing profile properties and update editable fields.
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
                "The profile could not be saved.",
            )
            return

        # Update the password in the system keyring.
        if not set_nvr_password(profile_id, nvr_password):
            QMessageBox.critical(
                self,
                "Save Profile",
                "The profile data was saved, but the password could not "
                "be updated in the system keyring.\n\n"
                "The application will not restart. Check the keyring "
                "and verify the stored password before reconnecting.",
            )
            return

        # Restart only when the active profile has been modified.
        if profile_id == get_active_profile():
            QMessageBox.information(
                self,
                "Profile Updated",
                "The active profile was updated successfully.\n\n"
                "If you changed the connection parameters or password, "
                "make sure they also match the settings on the physical NVR.\n\n"
                "The application will now restart.",
            )

            os.execv(
                sys.executable,
                [sys.executable] + sys.argv,
            )

        else:
            QMessageBox.information(
                self,
                "Profile Updated",
                f"The profile '{profile_name}' was updated successfully.\n\n"
                "The changes have been saved and will take effect "
                "the next time you activate this profile.\n\n"
                "The application does not need to restart.",
            )

            self.load_profiles()
            self.cancel_profile_edit()

    # -----------------------------------------------------------------
    # Cancel profile editing
    # -----------------------------------------------------------------

    def cancel_profile_edit(self):
        """Exit editing mode and reset the profile form."""
        self.editing_profile_id = None
        self.editing_profile_name = None

        # Clear all form fields.
        self.profile_name.clear()
        self.nvr_username.clear()
        self.nvr_password.clear()
        self.nvr_password_confirm.clear()
        self.nvr_ip.clear()
        self.nvr_port.clear()
        self.nvr_channels.clear()

        # Restore the profile creation controls.
        self.editing_profile_label.hide()
        self.create_profile_button.show()
        self.save_profile_button.hide()
        self.cancel_edit_button.hide()

    # -----------------------------------------------------------------
    # Delete connection profiles
    # -----------------------------------------------------------------

    def delete_selected_profile(self):
        """Confirm and delete the selected connection profile."""
        selected_item = self.profile_list.currentItem()

        if selected_item is None:
            QMessageBox.information(
                self,
                "Delete Profile",
                "Please select a profile to delete.",
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
            QMessageBox.StandardButton.Cancel,
        )

        if reply != QMessageBox.StandardButton.Ok:
            return

        if not delete_profile(profile_id):
            QMessageBox.critical(
                self,
                "Delete Profile",
                "The profile could not be deleted.\n\n"
                "Make sure the selected profile is not the active profile.",
            )
            return

        self.load_profiles()

        QMessageBox.information(
            self,
            "Delete Profile",
            "The profile was deleted successfully.",
        )

    # -----------------------------------------------------------------
    # Create connection profiles
    # -----------------------------------------------------------------

    def create_new_profile(self):
        """Validate the form and create a new connection profile."""
        # Read the values entered in the form.
        profile_name = self.profile_name.text().strip()
        nvr_user = self.nvr_username.text().strip()
        nvr_password = self.nvr_password.text()
        nvr_password_confirm = self.nvr_password_confirm.text()
        nvr_ip = self.nvr_ip.text().strip()
        nvr_port = self.nvr_port.text().strip()
        nvr_channels = self.nvr_channels.text().strip()

        # Validate password fields.
        if not nvr_password:
            print("Error al crear perfil: la contraseña es obligatoria")
            return

        if not nvr_password_confirm:
            print("Error al crear perfil: falta confirmar la contraseña")
            return

        if any(char.isspace() for char in nvr_password):
            print(
                "Error al crear perfil: "
                "la contraseña no puede contener espacios"
            )
            return

        if nvr_password != nvr_password_confirm:
            print("Error al crear perfil: las contraseñas no coinciden")
            return

        # Validate the remaining profile fields.
        valid, error = validate_profile(
            profile_name,
            nvr_user,
            nvr_ip,
            nvr_port,
            nvr_channels,
        )

        if not valid:
            print(f"Error al crear perfil: {error}")
            return

        # Generate a unique profile identifier.
        profiles = get_profiles()
        profile_id = generate_profile_id(profile_name)

        if profile_id in profiles:
            print("Error al crear perfil: ese nombre ya existe")
            return

        # Build the new profile from the default configuration.
        profile_data = get_default_profile()

        profile_data["name"] = profile_name
        profile_data["NVR_USER"] = nvr_user
        profile_data["NVR_IP"] = nvr_ip
        profile_data["NVR_PORT"] = nvr_port
        profile_data["TOTAL_CHANNELS"] = int(nvr_channels)

        if not create_profile(profile_id, profile_data):
            print("Error al crear el perfil")
            return

        # Store the password in the system keyring.
        if nvr_password:
            set_nvr_password(profile_id, nvr_password)

        # Refresh the profile list and reset the form.
        self.load_profiles()

        self.profile_name.clear()
        self.nvr_username.clear()
        self.nvr_password.clear()
        self.nvr_password_confirm.clear()
        self.nvr_ip.clear()
        self.nvr_port.clear()
        self.nvr_channels.clear()

        print(f"Perfil creado correctamente: {profile_name}")

    # -----------------------------------------------------------------
    # Activate connection profiles
    # -----------------------------------------------------------------

    def activate_profile(self):
        """Activate the selected profile and restart the application."""
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
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        if not set_active_profile(profile_id):
            QMessageBox.critical(
                self,
                "Error",
                "The active profile could not be changed.",
            )
            return

        os.execv(
            sys.executable,
            [sys.executable] + sys.argv,
        )
