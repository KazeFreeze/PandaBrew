from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QProgressBar,
    QFrame, QGroupBox, QLineEdit, QTextEdit, QRadioButton, QCheckBox,
    QTreeView, QScrollArea
)

class UIComponents:
    def __init__(self, main_window):
        self.main_window = main_window

    def create_main_layout(self):
        # The main layout is already part of MainWindow, we just add the bottom bar
        self.create_bottom_bar()

    def create_bottom_bar(self):
        bottom_bar_frame = QFrame()
        bottom_bar_frame.setLayout(QHBoxLayout())
        bottom_bar_frame.layout().setContentsMargins(10, 0, 10, 10)

        self.main_window.status_label = QLabel("Ready")
        bottom_bar_frame.layout().addWidget(self.main_window.status_label)

        self.main_window.progress = QProgressBar()
        self.main_window.progress.setVisible(False)
        bottom_bar_frame.layout().addWidget(self.main_window.progress)

        self.main_window.extract_btn = QPushButton("Extract Code")
        bottom_bar_frame.layout().addWidget(self.main_window.extract_btn)

        self.main_window.cancel_btn = QPushButton("Cancel")
        self.main_window.cancel_btn.setVisible(False)
        bottom_bar_frame.layout().addWidget(self.main_window.cancel_btn)

        self.main_window.layout.addWidget(bottom_bar_frame)

    def create_tab_ui(self, tab_widget):
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)

        options_container = QGroupBox("Directory & Options")
        options_layout = QVBoxLayout(options_container)
        main_layout.addWidget(options_container)

        self.create_path_selection(options_layout)
        self.create_options_section(options_layout)

        filter_container = QGroupBox("Per-Tab Filter Patterns")
        self._create_filter_settings(filter_container)
        main_layout.addWidget(filter_container)

        tree_container = QGroupBox("Project Structure")
        tree_layout = QVBoxLayout(tree_container)
        main_layout.addWidget(tree_container)

        self.create_tree_view(tree_layout)
        self._create_tree_control_buttons(tree_layout)

        tab_widget.addTab(main_container, "New Tab")

    def create_path_selection(self, parent_layout):
        path_frame = QFrame()
        path_layout = QHBoxLayout(path_frame)

        source_label = QLabel("Source:")
        source_entry = QLineEdit()
        browse_source_btn = QPushButton("Browse")

        output_label = QLabel("Output:")
        output_entry = QLineEdit()
        browse_output_btn = QPushButton("Save As")

        path_layout.addWidget(source_label)
        path_layout.addWidget(source_entry)
        path_layout.addWidget(browse_source_btn)
        path_layout.addWidget(output_label)
        path_layout.addWidget(output_entry)
        path_layout.addWidget(browse_output_btn)

        parent_layout.addWidget(path_frame)

    def create_options_section(self, parent_layout):
        options_frame = QFrame()
        options_layout = QHBoxLayout(options_frame)

        mode_group = QGroupBox("Selection Mode:")
        mode_layout = QHBoxLayout(mode_group)
        include_radio = QRadioButton("Include checked")
        exclude_radio = QRadioButton("Exclude checked")
        include_radio.setChecked(True)
        mode_layout.addWidget(include_radio)
        mode_layout.addWidget(exclude_radio)

        output_group = QGroupBox("Output Options:")
        output_layout = QHBoxLayout(output_group)
        filenames_only_check = QCheckBox("Filenames only")
        show_excluded_check = QCheckBox("Show excluded in structure")
        output_layout.addWidget(filenames_only_check)
        output_layout.addWidget(show_excluded_check)

        options_layout.addWidget(mode_group)
        options_layout.addWidget(output_group)
        parent_layout.addWidget(options_frame)

    def _create_filter_settings(self, parent_group):
        filter_layout = QHBoxLayout(parent_group)

        exclude_group = QGroupBox("Exclude Patterns")
        exclude_layout = QVBoxLayout(exclude_group)
        exclude_text = QTextEdit()
        exclude_layout.addWidget(exclude_text)

        include_group = QGroupBox("Include Patterns (Overrides Exclude)")
        include_layout = QVBoxLayout(include_group)
        include_text = QTextEdit()
        include_layout.addWidget(include_text)

        filter_layout.addWidget(exclude_group)
        filter_layout.addWidget(include_group)

    def create_tree_view(self, parent_layout):
        tree_view = QTreeView()
        parent_layout.addWidget(tree_view)

    def _create_tree_control_buttons(self, parent_layout):
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)

        select_all_btn = QPushButton("Select All")
        deselect_all_btn = QPushButton("Deselect All")
        refresh_btn = QPushButton("Refresh")

        controls_layout.addWidget(select_all_btn)
        controls_layout.addWidget(deselect_all_btn)
        controls_layout.addWidget(refresh_btn)

        parent_layout.addWidget(controls_frame)