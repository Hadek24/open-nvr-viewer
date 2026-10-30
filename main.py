import sys
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication
from src.app_window.main_window import MainWindow
from src.app_window.resource_utils import resource_path

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("resources/app_icon.png")))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
