import sys
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox
from src.app_window.main_window import MainWindow
from src.app_window.resource_utils import resource_path
from src.auth_dialogs import InitialSuperadminDialog, LoginDialog
from src.user_manager import UserManager
from src.config import load_raw_config

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("resources/app_icon.png")))

    try:
        user_manager = UserManager()
        administration = user_manager.get_administration_state()
    except (OSError, ValueError) as error:
        QMessageBox.critical(
            None,
            "Local account storage error",
            f"Open NVR Viewer cannot read users.json:\n{error}\n\n"
            "No account data was changed.",
        )
        return 1

    if administration["status"] in ("first_run", "bootstrap_required"):
        existing_users = administration["status"] == "bootstrap_required"
        setup = InitialSuperadminDialog(existing_users=existing_users)
        if not setup.exec():
            return 0
        username, password = setup.get_credentials()
        try:
            user_manager.create_initial_superadmin(username, password)
        except (OSError, ValueError) as error:
            QMessageBox.critical(None, "Superadmin creation failed", str(error))
            return 1

    elif administration["status"] == "recovery_required":
        QMessageBox.critical(
            None,
            "Account recovery required",
            "The local account database has an inconsistent Superadmin state. "
            "For safety, the application will not modify users.json automatically.",
        )
        return 1

    login = LoginDialog(user_manager)
    if not login.exec():
        return 0

    raw_config = load_raw_config()
    has_profiles = (
        isinstance(raw_config, dict)
        and isinstance(raw_config.get("profiles"), dict)
        and bool(raw_config.get("profiles"))
    )
    if not has_profiles and login.session_user["role"] != "Superadmin":
        QMessageBox.warning(
            None,
            "Configuration required",
            "The Superadmin must create the first NVR profile before "
            "Administrator or Viewer accounts can access the application.",
        )
        return 0

    window = MainWindow(login.session_user)
    window.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
