from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QProgressBar, QFrame

class UIComponents:
    def __init__(self, main_window):
        self.main_window = main_window
        self.extract_btn = None
        self.cancel_btn = None
        self.progress = None
        self.status_label = None

    def create_main_layout(self):
        # The main layout is already part of MainWindow, we just add the bottom bar
        self.create_bottom_bar()

    def create_bottom_bar(self):
        bottom_bar_frame = QFrame()
        bottom_bar_layout = QHBoxLayout(bottom_bar_frame)
        bottom_bar_layout.setContentsMargins(10, 0, 10, 10)

        self.status_label = QLabel("Ready")
        bottom_bar_layout.addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        bottom_bar_layout.addWidget(self.progress)

        self.extract_btn = QPushButton("Extract Code")
        bottom_bar_layout.addWidget(self.extract_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setVisible(False)
        bottom_bar_layout.addWidget(self.cancel_btn)

        self.main_window.main_layout.addWidget(bottom_bar_frame)

    def create_tab_ui(self, tab_widget):
        # This will be filled in to create the UI for each tab
        pass