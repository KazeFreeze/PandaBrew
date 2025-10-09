import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSplitter,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt, QFile, QTextStream
from pathlib import Path
import uuid

from .widgets import ControlPanel
from .qt_tree_view_manager import QtTreeViewManager
from ..config_manager import ConfigManager
from ..threaded_file_processor import ThreadedFileProcessor


class MainWindow(QMainWindow):
    def __init__(self, app_instance):
        super().__init__()
        self.app = app_instance
        self.setWindowTitle("PandaBrew")
        self.setGeometry(100, 100, 1200, 800)

        self.config_manager = ConfigManager(self)
        self.file_processor = ThreadedFileProcessor(self)
        self.config = self.config_manager.load_app_state()

        # App state variables
        self.include_mode = self.config.get("include_mode", True)
        self.filenames_only = self.config.get("filenames_only", False)
        self.show_excluded_in_structure = self.config.get("show_excluded_in_structure", True)

        self._load_stylesheet()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Main horizontal layout
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(5)

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.main_layout.addWidget(self.tab_widget)

        self._create_tab_control_buttons()

        self.tabs = {}
        self.add_new_tab()

    def _create_tab_control_buttons(self):
        """Creates the '+', 'x', and '?' buttons for tab management."""
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(5)

        self.add_tab_btn = QPushButton("+")
        self.add_tab_btn.clicked.connect(self.add_new_tab)
        self.close_tab_btn = QPushButton("✕")
        self.close_tab_btn.clicked.connect(self.close_current_tab)
        self.help_btn = QPushButton("?")
        self.help_btn.clicked.connect(self.show_filter_help)

        self.add_tab_btn.setFixedSize(30, 30)
        self.close_tab_btn.setFixedSize(30, 30)
        self.help_btn.setFixedSize(30, 30)

        button_layout.addWidget(self.add_tab_btn)
        button_layout.addWidget(self.close_tab_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.help_btn)

        self.main_layout.addWidget(button_container)

    def _load_stylesheet(self):
        style_file = QFile("app/qt_app/styles.qss")
        if style_file.open(QFile.ReadOnly | QFile.Text):
            stream = QTextStream(style_file)
            self.app.setStyleSheet(stream.readAll())

    def add_new_tab(self, source_path=None):
        tab_id = str(uuid.uuid4())
        tab = QWidget()
        tab.layout = QVBoxLayout(tab)

        splitter = QSplitter(Qt.Horizontal)

        control_panel = ControlPanel()
        tree_view_manager = QtTreeViewManager(tab_id)

        splitter.addWidget(control_panel)
        splitter.addWidget(tree_view_manager)
        splitter.setSizes([350, 850])

        tab.layout.addWidget(splitter)

        self.tabs[tab_id] = {
            "widget": tab,
            "control_panel": control_panel,
            "tree_view_manager": tree_view_manager,
        }

        tab_name = Path(source_path).name if source_path else "New Tab"
        self.tab_widget.addTab(tab, tab_name)
        self.tab_widget.setCurrentWidget(tab)

        self._connect_signals(control_panel)

    def _connect_signals(self, cp):
        cp.browse_source_btn.clicked.connect(self.browse_source)
        cp.browse_output_btn.clicked.connect(self.browse_output)
        cp.extract_btn.clicked.connect(self.file_processor.process_files)
        cp.cancel_btn.clicked.connect(self.file_processor.cancel_processing)

        cp.include_mode_radio.toggled.connect(lambda checked: self.set_include_mode(checked))
        cp.filenames_only_checkbox.toggled.connect(lambda checked: setattr(self, 'filenames_only', checked))
        cp.show_excluded_checkbox.toggled.connect(lambda checked: setattr(self, 'show_excluded_in_structure', checked))

    def set_include_mode(self, is_include):
        self.include_mode = is_include

    def get_processing_parameters(self):
        active_tab = self.get_active_tab()
        if not active_tab: return {}

        cp = active_tab["control_panel"]
        tm = active_tab["tree_view_manager"]

        manual_selections = tm.get_checked_paths()

        return {
            "source": cp.source_path.text(),
            "output": cp.output_path.text(),
            "include_mode": self.include_mode,
            "manual_selections": manual_selections,
            "include_patterns": [p.strip() for p in cp.include_patterns_text.toPlainText().splitlines() if p.strip()],
            "exclude_patterns": [p.strip() for p in cp.exclude_patterns_text.toPlainText().splitlines() if p.strip()],
            "filenames_only": self.filenames_only,
            "show_excluded": self.show_excluded_in_structure,
        }

    def close_tab(self, index):
        widget = self.tab_widget.widget(index)
        tab_id_to_close = next((tid for tid, tdata in self.tabs.items() if tdata["widget"] == widget), None)
        if tab_id_to_close:
            del self.tabs[tab_id_to_close]
        self.tab_widget.removeTab(index)
        if self.tab_widget.count() == 0:
            self.add_new_tab()

    def get_active_tab(self):
        active_widget = self.tab_widget.currentWidget()
        return next((tdata for tdata in self.tabs.values() if tdata["widget"] == active_widget), None)

    def browse_source(self):
        active_tab = self.get_active_tab()
        if not active_tab: return
        folder = QFileDialog.getExistingDirectory(self, "Select Source Directory")
        if folder:
            active_tab["control_panel"].source_path.setText(folder)
            active_tab["tree_view_manager"].load_directory(folder)
            self.tab_widget.setTabText(self.tab_widget.currentIndex(), Path(folder).name)

    def browse_output(self):
        active_tab = self.get_active_tab()
        if not active_tab: return
        file, _ = QFileDialog.getSaveFileName(self, "Save As", "", "Text files (*.txt);;All files (*.*)")
        if file:
            active_tab["control_panel"].output_path.setText(file)

    # --- Slots for backend signals ---
    def update_progress(self, value, status):
        active_tab = self.get_active_tab()
        if active_tab:
            active_tab["control_panel"].progress_bar.setValue(value)
            active_tab["control_panel"].status_label.setText(status)

    def on_processing_complete(self, title, message, count):
        self.file_processor.is_processing = False
        self.set_ui_processing_state(False)
        self.update_progress(100, f"Complete. {count} files processed.")
        QMessageBox.information(self, title, message)

    def on_processing_error(self, error_message):
        self.file_processor.is_processing = False
        self.set_ui_processing_state(False)
        self.update_progress(0, "Error occurred")
        QMessageBox.critical(self, "Error", error_message)

    def on_processing_cancelled(self):
        self.file_processor.is_processing = False
        self.set_ui_processing_state(False)
        self.update_progress(0, "Operation cancelled")

    def set_ui_processing_state(self, is_processing):
        active_tab = self.get_active_tab()
        if not active_tab: return
        control_panel = active_tab["control_panel"]
        if is_processing:
            control_panel.extract_btn.setEnabled(False)
            control_panel.cancel_btn.show()
        else:
            control_panel.extract_btn.setEnabled(True)
            control_panel.cancel_btn.hide()

    def closeEvent(self, event):
        self.on_closing()
        event.accept()

    def on_closing(self):
        if self.file_processor.is_processing:
            reply = QMessageBox.question(self, 'Processing in Progress',
                                           "An extraction is currently running. Are you sure you want to quit?",
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return
            self.file_processor.cancel_processing()
        self.config_manager.save_app_state()

    def close_current_tab(self):
        """Closes the currently active tab."""
        current_index = self.tab_widget.currentIndex()
        if current_index != -1:
            self.close_tab(current_index)

    def show_filter_help(self):
        """Displays a dialog with help text for filter patterns."""
        pipeline_explanation = (
            "<b>Filter Precedence Pipeline</b><br><br>"
            "Filters are applied in the following order:<br><br>"
            "1. <b>Manual Selections</b>: The initial set of files is determined by the "
            "checked items in the tree view and the 'Include/Exclude' mode.<br><br>"
            "2. <b>Exclude Patterns</b>: Files matching these patterns are <b>removed</b> from the set.<br><br>"
            "3. <b>Include Patterns</b>: Files matching these patterns are <b>added back</b> to the set, "
            "overriding any previous exclusions."
        )
        syntax_explanation = (
            "<br><br><b>Pattern Syntax</b><br><br>"
            "Patterns use glob-style matching, similar to .gitignore.<br><br>"
            "- <code>*</code> matches everything<br>"
            "- <code>?</code> matches any single character<br>"
            "- <code>[seq]</code> matches any character in seq<br>"
            "- <code>[!seq]</code> matches any character not in seq<br><br>"
            "<b>Examples</b><br><br>"
            "- <code>*.py</code>: Matches all Python files.<br>"
            "- <code>src/*</code>: Matches all files in the <code>src</code> directory.<br>"
            "- <code>__pycache__/</code>: Matches the pycache directory.<br>"
        )
        help_text = pipeline_explanation + syntax_explanation
        QMessageBox.information(self, "Filter Help", help_text)
