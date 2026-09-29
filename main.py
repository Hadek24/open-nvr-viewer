import sys
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication
from src.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("resources/app_icon.png"))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
