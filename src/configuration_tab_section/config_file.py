"""Configuration file management section for Open NVR Viewer."""

import os
import sys
import base64
import json
import secrets

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox,
    QScrollArea,
    QFileDialog,
    QInputDialog,
    QLineEdit,
)

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.exceptions import InvalidTag

from src.config import (
    create_config,
    get_config_path,
    get_config_dir,
    delete_config,
    load_raw_config,
    get_nvr_password,
    get_nvr_password_for_backup,
    set_nvr_password,
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
        
        # Separador entre el File mgmt Y la importacion y exportacion..
        self.separator_3 = QLabel()
        self.separator_3.setFixedHeight(1)
        self.separator_3.setStyleSheet(configuration_separator_style)
        
        self.content_layout.addSpacing(8)
        self.content_layout.addWidget(self.separator_3)
        self.content_layout.addSpacing(8)
        
        # --- Subsección de importación y exportación ---
        self.import_export_title = QLabel("Configuration Import/Export Management")
        self.import_export_title.setStyleSheet(configuration_subsection_title_style)
        self.content_layout.addWidget(self.import_export_title)

        self.content_layout.addSpacing(8)
        
        self._add_action_row(
            "Import configuration file:",
            "Import",
            self.import_config_file,
        )
        self._add_action_row(
            "Export configuration file:",
            "Export",
            self.export_config_file,
        )
        self._add_action_row(
            "Verify backup file:",
            "Select",
            self.verify_config_file,
        )
        
        # Separador final.
        self.separator_4 = QLabel()
        self.separator_4.setFixedHeight(1)
        self.separator_4.setStyleSheet(configuration_separator_style)
        
        self.content_layout.addSpacing(8)
        self.content_layout.addWidget(self.separator_4)
        self.content_layout.addSpacing(8)
        
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

    def import_config_file(self):
        """Import and validate an encrypted configuration backup."""

        # Select the backup file.
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Configuration Backup",
            os.path.expanduser("~"),
            "Open NVR Viewer Backup (*.nvrbackup)",
        )

        if not file_path:
            return

        try:
            # Read the backup file.
            with open(file_path, "r", encoding="utf-8") as backup_file:
                envelope = json.load(backup_file)

            # Validate the backup envelope.
            if not isinstance(envelope, dict):
                raise ValueError("The backup file format is invalid.")

            if envelope.get("format") != "open-nvr-viewer-encrypted-backup":
                raise ValueError("The selected file is not a supported backup.")

            if envelope.get("version") != 1:
                raise ValueError("The backup version is not supported.")

            if envelope.get("kdf") != "scrypt":
                raise ValueError("The backup key derivation method is unsupported.")

            if envelope.get("cipher") != "AES-256-GCM":
                raise ValueError("The backup encryption method is unsupported.")

            kdf_params = envelope.get("kdf_params")

            if kdf_params != {"n": 2**14, "r": 8, "p": 1}:
                raise ValueError("The backup encryption parameters are invalid.")

            salt = base64.b64decode(envelope["salt"], validate=True)
            nonce = base64.b64decode(envelope["nonce"], validate=True)
            ciphertext = base64.b64decode(
                envelope["ciphertext"],
                validate=True,
            )

            if len(salt) != 16 or len(nonce) != 12 or len(ciphertext) < 16:
                raise ValueError("The backup encryption data is invalid.")

        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            QMessageBox.warning(
                self,
                "Import Configuration",
                f"The backup file could not be read:\n{error}",
            )
            return

        # Ask for the master password.
        password, ok = QInputDialog.getText(
            self,
            "Unlock Backup",
            "Enter the backup master password:",
            QLineEdit.EchoMode.Password,
        )

        if not ok:
            return

        try:
            # Derive the encryption key.
            kdf = Scrypt(
                salt=salt,
                length=32,
                n=2**14,
                r=8,
                p=1,
            )

            key = kdf.derive(password.encode("utf-8"))

            # Decrypt the backup.
            aesgcm = AESGCM(key)

            plaintext = aesgcm.decrypt(
                nonce,
                ciphertext,
                b"open-nvr-viewer-backup-v1",
            )

            backup_data = json.loads(plaintext.decode("utf-8"))

            # Validate the decrypted backup contents.
            if not isinstance(backup_data, dict):
                raise ValueError("The decrypted backup content is invalid.")

            if backup_data.get("format") != "open-nvr-viewer-backup":
                raise ValueError("The backup content format is unsupported.")

            if backup_data.get("version") != 1:
                raise ValueError("The backup content version is unsupported.")

            config = backup_data.get("config")
            credentials = backup_data.get("credentials")

            if not isinstance(config, dict):
                raise ValueError("The backup configuration is invalid.")

            profiles = config.get("profiles")

            if not isinstance(profiles, dict) or not profiles:
                raise ValueError("The backup contains no valid profiles.")

            if not isinstance(credentials, dict):
                raise ValueError("The backup credentials are invalid.")

            if any(
                not isinstance(profile_id, str)
                or not isinstance(profile, dict)
                for profile_id, profile in profiles.items()
            ):
                raise ValueError("The backup contains an invalid profile.")

            if any(
                not isinstance(profile_id, str)
                or not isinstance(secret, str)
                for profile_id, secret in credentials.items()
            ):
                raise ValueError("The backup contains invalid credentials.")

            if set(credentials) != set(profiles):
                raise ValueError(
                    "The backup does not contain credentials for every profile."
                )

        except InvalidTag:
            QMessageBox.warning(
                self,
                "Import Configuration",
                "The master password is incorrect or the backup has been modified.",
            )
            return

        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
        ) as error:
            QMessageBox.warning(
                self,
                "Import Configuration",
                f"The backup contents are invalid:\n{error}",
            )
            return

        # Confirm before restoring the backup.
        answer = QMessageBox.question(
            self,
            "Restore Configuration",
            "The backup is valid and contains "
            f"{len(profiles)} profile(s).\n\n"
            "Restoring it will replace the current configuration "
            "and update the saved profile passwords.\n\n"
            "Do you want to continue?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            # Restore the profile passwords to the system keyring.
            for profile_id, profile_password in credentials.items():
                if not set_nvr_password(profile_id, profile_password):
                    raise RuntimeError(
                        f"Could not restore the password for "
                        f"profile '{profile_id}'."
                    )

            # Prepare the configuration file.
            config_path = get_config_path()
            config_dir = os.path.dirname(config_path)

            os.makedirs(config_dir, exist_ok=True)

            # Write to a temporary file first.
            temp_path = config_path + ".tmp"

            try:
                with open(temp_path, "w", encoding="utf-8") as config_file:
                    json.dump(
                        config,
                        config_file,
                        indent=4,
                        ensure_ascii=False,
                    )

                # Replace the current configuration atomically.
                os.replace(temp_path, config_path)

            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        except Exception as error:
            QMessageBox.critical(
                self,
                "Restore Configuration",
                "The configuration could not be fully restored.\n\n"
                f"Details: {error}\n\n"
                "Some passwords may already have been updated. "
                "Check the current configuration before trying again.",
            )
            return

        QMessageBox.information(
            self,
            "Restore Configuration",
            f"The backup was restored successfully.\n\n"
            f"Profiles restored: {len(profiles)}\n"
            "The configuration and saved passwords have been restored.\n\n"
            "The application will now restart.",
        )

        os.execv(
            sys.executable,
            [sys.executable] + sys.argv,
        )

    def export_config_file(self):
        """Export the configuration and available credentials securely."""

        config = load_raw_config()

        if not isinstance(config, dict):
            QMessageBox.warning(
                self,
                "Export Configuration",
                "No configuration file was found.",
            )
            return

        profiles = config.get("profiles")

        if not isinstance(profiles, dict):
            QMessageBox.warning(
                self,
                "Export Configuration",
                "The configuration format is not supported.",
            )
            return

        # Ask for the master password.
        password, ok = QInputDialog.getText(
            self,
            "Protect Backup",
            "Enter a master password (minimum 12 characters):",
            QLineEdit.EchoMode.Password,
        )

        if not ok:
            return

        if len(password) < 12:
            QMessageBox.warning(
                self,
                "Protect Backup",
                "The master password must contain at least "
                "12 characters.",
            )
            return

        confirmation, ok = QInputDialog.getText(
            self,
            "Confirm Master Password",
            "Enter the master password again:",
            QLineEdit.EchoMode.Password,
        )

        if not ok:
            return

        if password != confirmation:
            QMessageBox.warning(
                self,
                "Protect Backup",
                "The passwords do not match.",
            )
            return

        # Choose the backup destination.
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Configuration Backup",
            os.path.join(
                os.path.expanduser("~"),
                "open-nvr-viewer.nvrbackup",
            ),
            "Open NVR Viewer Backup (*.nvrbackup)",
        )

        if not file_path:
            return

        if not file_path.lower().endswith(".nvrbackup"):
            file_path += ".nvrbackup"

        try:
            # Collect credentials from the system keyring.
            credentials = {}

            for profile_id in profiles:
                profile_password = get_nvr_password_for_backup(profile_id)

                if profile_password is None:
                    raise ValueError(
                        f"No password was found for profile '{profile_id}'. "
                        "The backup cannot be created."
                    )

                credentials[profile_id] = profile_password

            # Build the data to protect.
            backup_data = {
                "format": "open-nvr-viewer-backup",
                "version": 1,
                "config": config,
                "credentials": credentials,
            }

            plaintext = json.dumps(
                backup_data,
                ensure_ascii=False,
            ).encode("utf-8")

            # Derive an encryption key from the master password.
            salt = secrets.token_bytes(16)

            kdf = Scrypt(
                salt=salt,
                length=32,
                n=2**14,
                r=8,
                p=1,
            )

            key = kdf.derive(password.encode("utf-8"))

            # Encrypt using AES-256-GCM.
            nonce = secrets.token_bytes(12)

            associated_data = b"open-nvr-viewer-backup-v1"

            ciphertext = AESGCM(key).encrypt(
                nonce,
                plaintext,
                associated_data,
            )

            # Store only the encryption metadata and ciphertext.
            envelope = {
                "format": "open-nvr-viewer-encrypted-backup",
                "version": 1,
                "kdf": "scrypt",
                "kdf_params": {
                    "n": 2**14,
                    "r": 8,
                    "p": 1,
                },
                "cipher": "AES-256-GCM",
                "salt": base64.b64encode(salt).decode("ascii"),
                "nonce": base64.b64encode(nonce).decode("ascii"),
                "ciphertext": base64.b64encode(
                    ciphertext
                ).decode("ascii"),
            }

            with open(file_path, "x", encoding="utf-8") as backup_file:
                json.dump(
                    envelope,
                    backup_file,
                    indent=2,
                )

            QMessageBox.information(
                self,
                "Export Configuration",
                "The encrypted backup was created successfully.\n\n"
                "Keep your master password safe. It will be required "
                "to restore this backup.",
            )

        except FileExistsError:
            QMessageBox.warning(
                self,
                "Export Configuration",
                "The selected file already exists. "
                "Choose a different filename.",
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Export Configuration",
                f"The backup could not be created:\n{error}",
            )

    def verify_config_file(self):
        """Verify an encrypted backup without modifying application data."""

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Verify Configuration Backup",
            os.path.expanduser("~"),
            "Open NVR Viewer Backup (*.nvrbackup)",
        )

        if not file_path:
            return

        try:
            # Read the backup envelope.
            with open(file_path, "r", encoding="utf-8") as backup_file:
                envelope = json.load(backup_file)

            if not isinstance(envelope, dict):
                raise ValueError("Invalid backup structure.")

            if (
                envelope.get("format")
                != "open-nvr-viewer-encrypted-backup"
                or envelope.get("version") != 1
                or envelope.get("kdf") != "scrypt"
                or envelope.get("cipher") != "AES-256-GCM"
            ):
                raise ValueError("Unsupported backup format.")

            # Accept only the parameters used by our exporter.
            expected_params = {
                "n": 2**14,
                "r": 8,
                "p": 1,
            }

            if envelope.get("kdf_params") != expected_params:
                raise ValueError("Unsupported encryption parameters.")

            # Decode and validate the encryption metadata.
            salt = base64.b64decode(
                envelope["salt"],
                validate=True,
            )
            nonce = base64.b64decode(
                envelope["nonce"],
                validate=True,
            )
            ciphertext = base64.b64decode(
                envelope["ciphertext"],
                validate=True,
            )

            if len(salt) != 16 or len(nonce) != 12:
                raise ValueError("Invalid encryption metadata.")

            if len(ciphertext) < 16:
                raise ValueError("Invalid encrypted content.")

        except (OSError, UnicodeError, ValueError, KeyError, TypeError) as error:
            QMessageBox.warning(
                self,
                "Backup Verification",
                "The selected file is invalid, damaged, or uses an "
                "unsupported backup format.\n\n"
                f"Details: {error}",
            )
            return

        # Request the master password.
        password, ok = QInputDialog.getText(
            self,
            "Verify Backup",
            "Enter the backup master password:",
            QLineEdit.EchoMode.Password,
        )

        if not ok:
            return

        if not password:
            QMessageBox.warning(
                self,
                "Backup Verification",
                "The master password cannot be empty.",
            )
            return

        try:
            # Derive the encryption key.
            kdf = Scrypt(
                salt=salt,
                length=32,
                n=2**14,
                r=8,
                p=1,
            )

            key = kdf.derive(password.encode("utf-8"))

            # Decrypt and authenticate the backup.
            plaintext = AESGCM(key).decrypt(
                nonce,
                ciphertext,
                b"open-nvr-viewer-backup-v1",
            )

        except InvalidTag:
            QMessageBox.warning(
                self,
                "Backup Verification",
                "Verification failed.\n\n"
                "The master password is incorrect, or the backup "
                "has been modified or damaged.",
            )
            return

        except Exception:
            QMessageBox.warning(
                self,
                "Backup Verification",
                "The backup could not be decrypted.",
            )
            return

        try:
            # Validate the decrypted backup structure.
            backup_data = json.loads(plaintext.decode("utf-8"))

            if not isinstance(backup_data, dict):
                raise ValueError("Invalid backup data.")

            if (
                backup_data.get("format") != "open-nvr-viewer-backup"
                or backup_data.get("version") != 1
            ):
                raise ValueError("Unsupported backup data version.")

            config = backup_data.get("config")
            credentials = backup_data.get("credentials")

            if not isinstance(config, dict):
                raise ValueError("Invalid configuration data.")

            profiles = config.get("profiles")

            if not isinstance(profiles, dict):
                raise ValueError("Invalid profiles structure.")

            if not isinstance(credentials, dict):
                raise ValueError("Invalid credentials structure.")

            if not all(
                isinstance(profile_id, str)
                and isinstance(profile, dict)
                for profile_id, profile in profiles.items()
            ):
                raise ValueError("Invalid profile entry.")

            if not all(
                isinstance(profile_id, str)
                and isinstance(profile_password, str)
                and profile_id in profiles
                for profile_id, profile_password in credentials.items()
            ):
                raise ValueError("Invalid credential entry.")

            active_profile = config.get("active_profile")

            if (
                active_profile is not None
                and active_profile not in profiles
            ):
                raise ValueError("Invalid active profile.")

        except (UnicodeError, ValueError, TypeError, KeyError) as error:
            QMessageBox.warning(
                self,
                "Backup Verification",
                "The file was decrypted, but its contents are invalid.\n\n"
                f"Details: {error}",
            )
            return

        # Verification succeeded. Nothing has been imported or changed.
        QMessageBox.information(
            self,
            "Backup Verification",
            "Backup verified successfully!\n\n"
            "The master password is correct, the encrypted content "
            "passed its integrity check, and the backup structure "
            "is valid.\n\n"
            "No application configuration or credentials were changed.",
        )

