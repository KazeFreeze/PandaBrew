from app.qt_app.main_window import MainWindow
from PySide6.QtWidgets import QApplication
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = MainWindow(app)
    main_win.show()
    sys.exit(app.exec())