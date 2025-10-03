from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QTextEdit, QRadioButton, QCheckBox, QTreeView, QGroupBox, QFrame
)
from .qt_tree_view_manager import QtTreeViewManager

class TabWidget(QWidget):
    """
    A custom widget that encapsulates all the UI and logic for a single tab.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tree_view_manager = None
        self._create_widgets()
        self._create_layouts()
        self._connect_signals()

    def _create_widgets(self):
        """Creates all the widgets for the tab."""
        # Path Selection
        self.source_label = QLabel("Source:")
        self.source_entry = QLineEdit()
        self.browse_source_btn = QPushButton("Browse")
        self.output_label = QLabel("Output:")
        self.output_entry = QLineEdit()
        self.browse_output_btn = QPushButton("Save As")

        # Options
        self.include_radio = QRadioButton("Include checked")
        self.exclude_radio = QRadioButton("Exclude checked")
        self.include_radio.setChecked(True)
        self.filenames_only_check = QCheckBox("Filenames only")
        self.show_excluded_check = QCheckBox("Show excluded in structure")
        self.show_excluded_check.setChecked(True)

        # Filter Patterns
        self.exclude_text = QTextEdit()
        self.include_text = QTextEdit()

        # Tree View
        self.tree_view = QTreeView()
        self.tree_view_manager = QtTreeViewManager(self.tree_view)
        self.select_all_btn = QPushButton("Select All")
        self.deselect_all_btn = QPushButton("Deselect All")
        self.refresh_btn = QPushButton("Refresh")

    def _create_layouts(self):
        """Creates the layout and arranges widgets."""
        main_layout = QVBoxLayout(self)

        # Directory & Options Group
        options_group = QGroupBox("Directory & Options")
        options_layout = QVBoxLayout(options_group)
        main_layout.addWidget(options_group)

        # Path Selection Layout
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.source_label)
        path_layout.addWidget(self.source_entry)
        path_layout.addWidget(self.browse_source_btn)
        path_layout.addWidget(self.output_label)
        path_layout.addWidget(self.output_entry)
        path_layout.addWidget(self.browse_output_btn)
        options_layout.addLayout(path_layout)

        # Options Layout
        options_frame_layout = QHBoxLayout()
        mode_group = QGroupBox("Selection Mode")
        mode_layout = QHBoxLayout(mode_group)
        mode_layout.addWidget(self.include_radio)
        mode_layout.addWidget(self.exclude_radio)
        output_options_group = QGroupBox("Output Options")
        output_options_layout = QHBoxLayout(output_options_group)
        output_options_layout.addWidget(self.filenames_only_check)
        output_options_layout.addWidget(self.show_excluded_check)
        options_frame_layout.addWidget(mode_group)
        options_frame_layout.addWidget(output_options_group)
        options_layout.addLayout(options_frame_layout)

        # Filter Patterns Group
        filter_group = QGroupBox("Per-Tab Filter Patterns")
        filter_layout = QHBoxLayout(filter_group)
        exclude_group = QGroupBox("Exclude Patterns")
        exclude_layout = QVBoxLayout(exclude_group)
        exclude_layout.addWidget(self.exclude_text)
        include_group = QGroupBox("Include Patterns (Overrides Exclude)")
        include_layout = QVBoxLayout(include_group)
        include_layout.addWidget(self.include_text)
        filter_layout.addWidget(exclude_group)
        filter_layout.addWidget(include_group)
        main_layout.addWidget(filter_group)

        # Project Structure Group
        tree_group = QGroupBox("Project Structure")
        tree_layout = QVBoxLayout(tree_group)
        tree_layout.addWidget(self.tree_view)
        # Tree Controls Layout
        tree_controls_layout = QHBoxLayout()
        tree_controls_layout.addWidget(self.select_all_btn)
        tree_controls_layout.addWidget(self.deselect_all_btn)
        tree_controls_layout.addWidget(self.refresh_btn)
        tree_controls_layout.addStretch()
        tree_layout.addLayout(tree_controls_layout)
        main_layout.addWidget(tree_group)

    def _connect_signals(self):
        """Connects widget signals to the appropriate slots."""
        self.select_all_btn.clicked.connect(self.tree_view_manager.select_all)
        self.deselect_all_btn.clicked.connect(self.tree_view_manager.deselect_all)

    def get_state(self) -> dict:
        """Returns the current state of the tab's UI controls."""
        return {
            "source_path": self.source_entry.text(),
            "output_path": self.output_entry.text(),
            "include_patterns": self.include_text.toPlainText().splitlines(),
            "exclude_patterns": self.exclude_text.toPlainText().splitlines(),
            "include_mode": self.include_radio.isChecked(),
            "filenames_only": self.filenames_only_check.isChecked(),
            "show_excluded": self.show_excluded_check.isChecked(),
            "manual_selections": self.tree_view_manager.checked_paths
        }

    def set_state(self, state: dict):
        """Sets the state of the tab's UI controls from a dictionary."""
        self.source_entry.setText(state.get("source_path", ""))
        self.output_entry.setText(state.get("output_path", ""))
        self.include_text.setPlainText("\n".join(state.get("include_patterns", [])))
        self.exclude_text.setPlainText("\n".join(state.get("exclude_patterns", [])))
        self.include_radio.setChecked(state.get("include_mode", True))
        self.filenames_only_check.setChecked(state.get("filenames_only", False))
        self.show_excluded_check.setChecked(state.get("show_excluded", True))

        self.tree_view_manager.checked_paths = set(state.get("manual_selections", []))

        if self.source_entry.text():
            self.tree_view_manager.refresh_tree(self.source_entry.text())