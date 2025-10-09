from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QCheckBox,
    QTextEdit,
    QProgressBar,
    QHBoxLayout,
    QFormLayout,
)


class ControlPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(10)

        self._create_path_selection()
        self._create_options_section()
        self._create_filter_settings()
        self._create_action_buttons()
        self._create_status_section()

        self.layout.addStretch()

    def _create_path_selection(self):
        group = QGroupBox("Directory & Options")
        layout = QFormLayout()

        self.source_path = QLineEdit()
        self.browse_source_btn = QPushButton("Browse")
        source_layout = QHBoxLayout()
        source_layout.addWidget(self.source_path)
        source_layout.addWidget(self.browse_source_btn)
        layout.addRow(QLabel("Source:"), source_layout)

        self.output_path = QLineEdit()
        self.browse_output_btn = QPushButton("Save As")
        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_path)
        output_layout.addWidget(self.browse_output_btn)
        layout.addRow(QLabel("Output:"), output_layout)

        group.setLayout(layout)
        self.layout.addWidget(group)

    def _create_options_section(self):
        group = QGroupBox("Selection & Output")
        layout = QHBoxLayout()

        # Mode Selection
        mode_group = QGroupBox("Selection Mode")
        mode_layout = QVBoxLayout()
        self.include_mode_radio = QRadioButton("Include checked")
        self.exclude_mode_radio = QRadioButton("Exclude checked")
        self.include_mode_radio.setChecked(True)
        mode_layout.addWidget(self.include_mode_radio)
        mode_layout.addWidget(self.exclude_mode_radio)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # Output Options
        options_group = QGroupBox("Output Options")
        options_layout = QVBoxLayout()
        self.filenames_only_checkbox = QCheckBox("Filenames only")
        self.show_excluded_checkbox = QCheckBox("Show excluded in structure")
        options_layout.addWidget(self.filenames_only_checkbox)
        options_layout.addWidget(self.show_excluded_checkbox)
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        group.setLayout(layout)
        self.layout.addWidget(group)

    def _create_filter_settings(self):
        group = QGroupBox("Per-Tab Filter Patterns")
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Exclude Patterns"))
        self.exclude_patterns_text = QTextEdit()
        self.exclude_patterns_text.setFixedHeight(80)
        layout.addWidget(self.exclude_patterns_text)

        layout.addWidget(QLabel("Include Patterns (Overrides Exclude)"))
        self.include_patterns_text = QTextEdit()
        self.include_patterns_text.setFixedHeight(80)
        layout.addWidget(self.include_patterns_text)

        group.setLayout(layout)
        self.layout.addWidget(group)

    def _create_action_buttons(self):
        self.action_layout = QHBoxLayout()
        self.extract_btn = QPushButton("Extract Code")
        self.extract_btn.setStyleSheet("background-color: green;")
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet("background-color: red;")
        self.cancel_btn.hide()
        self.action_layout.addWidget(self.extract_btn)
        self.action_layout.addWidget(self.cancel_btn)
        self.layout.addLayout(self.action_layout)

    def _create_status_section(self):
        status_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.status_label = QLabel("Ready")
        status_layout.addWidget(self.progress_bar)
        status_layout.addWidget(self.status_label)
        self.layout.addLayout(status_layout)
