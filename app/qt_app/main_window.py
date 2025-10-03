import darkdetect
from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QStyleFactory, QPushButton, QFrame
)
from .ui_components import UIComponents

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PandaBrew")
        self.setMinimumSize(QSize(900, 600))
        self.resize(1100, 750)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Main layout for the entire window
        self.main_layout = QVBoxLayout(self.central_widget)

        # Top frame for the notebook and tab buttons
        top_frame = QFrame()
        top_layout = QHBoxLayout(top_frame)
        top_layout.setContentsMargins(0, 0, 0, 0)

        self.notebook = QTabWidget()
        top_layout.addWidget(self.notebook)

        # Tab control buttons
        button_frame = QFrame()
        button_layout = QVBoxLayout(button_frame)
        self.add_tab_button = QPushButton("+")
        self.close_tab_button = QPushButton("✕")
        self.help_button = QPushButton("?")
        button_layout.addWidget(self.add_tab_button)
        button_layout.addWidget(self.close_tab_button)
        button_layout.addStretch()
        button_layout.addWidget(self.help_button)
        top_layout.addWidget(button_frame)

        self.main_layout.addWidget(top_frame)

        # Instantiate UIComponents and create the bottom bar
        self.ui_components = UIComponents(self)
        self.ui_components.create_main_layout() # This creates and adds the bottom bar

        # self.apply_styles() # Temporarily disabled for debugging

    def apply_styles(self):
        self.setStyle(QStyleFactory.create("Fusion"))
        try:
            if darkdetect.isDark():
                with open("styles/dark.qss", "r") as f:
                    self.setStyleSheet(f.read())
            else:
                with open("styles/light.qss", "r") as f:
                    self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Stylesheet not found. Using default styles.")