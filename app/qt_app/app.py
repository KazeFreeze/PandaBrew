import sys
import uuid
from pathlib import Path
from typing import Dict, Any, Optional

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from .main_window import MainWindow
from .tab_widget import TabWidget
from ..config_manager import ConfigManager
from ..threaded_file_processor import ThreadedFileProcessor

class AppSignals(QObject):
    """A simple QObject to hold signals for the app."""
    processing_requested = Signal(dict)

class PandaBrewQtApp:
    """
    The main application class for the PySide6-based PandaBrew.
    """
    def __init__(self):
        self.app = QApplication(sys.argv)

        # Set a more readable default font
        font = QFont("Segoe UI", 10)
        if sys.platform == "darwin":
            font = QFont("San Francisco", 10)
        elif sys.platform == "linux":
            font = QFont("Noto Sans", 10)
        self.app.setFont(font)

        self.signals = AppSignals()
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_app_state()

        self.main_window = MainWindow()
        self.main_window.resize(*self.config.get("window_geometry", {}).get("size", [1100, 750]))
        self.main_window.move(*self.config.get("window_geometry", {}).get("pos", [100, 100]))

        self.tabs: Dict[str, TabWidget] = {}

        self._setup_file_processor_thread()
        self._setup_event_bindings()
        self._load_tabs_from_config()

    def run(self):
        """Shows the main window and starts the application's event loop."""
        self.main_window.show()
        sys.exit(self.app.exec())

    def _setup_file_processor_thread(self):
        """Initializes the file processor and moves it to a separate thread."""
        self.file_processor = ThreadedFileProcessor()
        self.processor_thread = QThread()
        self.file_processor.moveToThread(self.processor_thread)

        self.signals.processing_requested.connect(self.file_processor.process_files)

        self.file_processor.signals.progress.connect(self._update_progress)
        self.file_processor.signals.complete.connect(self._on_processing_complete)
        self.file_processor.signals.error.connect(self._on_processing_error)
        self.file_processor.signals.cancelled.connect(self._on_processing_cancelled)

        self.processor_thread.start()

    def _setup_event_bindings(self):
        """Connects UI signals to application logic slots."""
        self.main_window.notebook.currentChanged.connect(self._on_tab_change)
        self.app.aboutToQuit.connect(self._on_closing)

        # Connect main window buttons
        self.main_window.add_tab_button.clicked.connect(self.add_new_tab)
        self.main_window.close_tab_button.clicked.connect(self.close_current_tab)
        self.main_window.help_button.clicked.connect(self.show_filter_help)

        self.main_window.ui_components.extract_btn.clicked.connect(self.start_processing)
        self.main_window.ui_components.cancel_btn.clicked.connect(self.file_processor.cancel_processing)

    def _load_tabs_from_config(self):
        """Loads tab information from the config and restores them."""
        open_tabs = self.config.get("open_tabs", [])
        active_tab_id = self.config.get("active_tab_id")

        if open_tabs and isinstance(open_tabs, list):
            for tab_info in open_tabs:
                if isinstance(tab_info, dict) and Path(tab_info.get("source_path", "")).exists():
                    self.add_new_tab(select_tab=False, state=tab_info)

        if not self.tabs:
            self.add_new_tab()

        if active_tab_id and active_tab_id in self.tabs:
            self.main_window.notebook.setCurrentWidget(self.tabs[active_tab_id])

    def add_new_tab(self, select_tab=True, state: Optional[Dict] = None):
        """Adds a new tab, creating the necessary widgets and data structures."""
        tab_id = state.get("id", str(uuid.uuid4())) if state else str(uuid.uuid4())
        tab_widget = TabWidget()

        if state:
            tab_widget.set_state(state)

        # Connect tab-specific signals
        tab_widget.browse_source_btn.clicked.connect(lambda: self.browse_source(tab_widget))
        tab_widget.browse_output_btn.clicked.connect(lambda: self.browse_output(tab_widget))
        tab_widget.refresh_btn.clicked.connect(lambda: self.refresh_tree(tab_widget))

        self.tabs[tab_id] = tab_widget

        tab_name = Path(tab_widget.source_entry.text()).name if tab_widget.source_entry.text() else "New Tab"
        tab_index = self.main_window.notebook.addTab(tab_widget, tab_name)

        if select_tab:
            self.main_window.notebook.setCurrentIndex(tab_index)

        return tab_id

    def close_current_tab(self):
        """Closes the currently active tab."""
        if self.main_window.notebook.count() <= 1:
            return

        current_widget = self.main_window.notebook.currentWidget()
        tab_id_to_close = next((tid for tid, twidget in self.tabs.items() if twidget == current_widget), None)

        if tab_id_to_close:
            self.main_window.notebook.removeTab(self.main_window.notebook.currentIndex())
            del self.tabs[tab_id_to_close]

    def get_active_tab(self) -> Optional[TabWidget]:
        """Returns the currently active TabWidget instance."""
        return self.main_window.notebook.currentWidget()

    def browse_source(self, tab_widget: TabWidget):
        """Opens a dialog to select a source directory for the given tab."""
        folder = QFileDialog.getExistingDirectory(self.main_window, "Select Source Directory")
        if folder:
            tab_widget.source_entry.setText(folder)
            for i in range(self.main_window.notebook.count()):
                if self.main_window.notebook.widget(i) == tab_widget:
                    self.main_window.notebook.setTabText(i, Path(folder).name)
                    break
            tab_widget.tree_view_manager.refresh_tree(folder)
            self._on_tab_change(self.main_window.notebook.currentIndex())

    def browse_output(self, tab_widget: TabWidget):
        """Opens a dialog to select an output file for the given tab."""
        file, _ = QFileDialog.getSaveFileName(self.main_window, "Save As", "", "Text files (*.txt);;All files (*.*)")
        if file:
            tab_widget.output_entry.setText(file)

    def refresh_tree(self, tab_widget: TabWidget):
        """Refreshes the tree view for the given tab."""
        source_path = tab_widget.source_entry.text()
        if source_path and Path(source_path).exists():
            tab_widget.tree_view_manager.refresh_tree(source_path)
        else:
            QMessageBox.warning(self.main_window, "Path Not Found", "The specified source path does not exist.")

    def show_filter_help(self):
        """Displays a dialog with help text for filter patterns."""
        pipeline_explanation = (
            "<b>Filter Precedence Pipeline</b><br>"
            "Filters are applied in the following order:<br><br>"
            "1. <b>Manual Selections</b>: The initial set of files is determined by the "
            "checked items in the tree view and the 'Include/Exclude' mode.<br><br>"
            "2. <b>Exclude Patterns</b>: Files matching these patterns are <b>removed</b> from the set.<br><br>"
            "3. <b>Include Patterns</b>: Files matching these patterns are <b>added back</b> to the set, "
            "overriding any previous exclusions."
        )
        syntax_explanation = (
            "<br><br><b>Pattern Syntax</b><br>"
            "Patterns use glob-style matching, similar to .gitignore.<br><br>"
            "- <code>*</code> matches everything<br>"
            "- <code>?</code> matches any single character<br>"
            "- <code>[seq]</code> matches any character in seq<br>"
            "- <code>[!seq]</code> matches any character not in seq<br><br>"
            "<b>Examples</b><br>"
            "- <code>*.py</code>: Matches all Python files.<br>"
            "- <code>src/*</code>: Matches all files in the <code>src</code> directory.<br>"
            "- <code>__pycache__/</code>: Matches the pycache directory.<br>"
        )
        help_text = pipeline_explanation + syntax_explanation
        QMessageBox.information(self.main_window, "Filter Help", help_text)

    def _on_tab_change(self, index: int):
        """Handles logic for when the active tab changes."""
        active_tab = self.get_active_tab()
        if active_tab:
            source_path = active_tab.source_entry.text()
            if source_path:
                self.main_window.setWindowTitle(f"PandaBrew - {Path(source_path).name}")
            else:
                self.main_window.setWindowTitle("PandaBrew")

    @Slot()
    def start_processing(self):
        """Gathers data from the active tab and starts the file processor."""
        active_tab = self.get_active_tab()
        if not active_tab:
            QMessageBox.critical(self.main_window, "Error", "No active tab found.")
            return

        tab_state = active_tab.get_state()
        if not tab_state["source_path"] or not tab_state["output_path"]:
            QMessageBox.critical(self.main_window, "Error", "Please select a source directory and an output file.")
            return

        self._set_ui_processing_state(True)
        self.signals.processing_requested.emit(tab_state)

    @Slot(int, str)
    def _update_progress(self, value, status):
        """Updates the progress bar and status label."""
        self.main_window.ui_components.progress.setVisible(True)
        self.main_window.ui_components.progress.setValue(value)
        self.main_window.ui_components.status_label.setText(status)

    @Slot(str, str, int)
    def _on_processing_complete(self, title, message, count):
        """Handles the completion of the file processing task."""
        self._set_ui_processing_state(False)
        self.main_window.ui_components.status_label.setText(f"Complete. {count} files processed.")
        QMessageBox.information(self.main_window, title, message)

    @Slot(str)
    def _on_processing_error(self, error_message):
        """Displays an error message if processing fails."""
        self._set_ui_processing_state(False)
        self.main_window.ui_components.status_label.setText("Error occurred")
        QMessageBox.critical(self.main_window, "Error", error_message)

    @Slot()
    def _on_processing_cancelled(self):
        """Resets the UI when processing is cancelled."""
        self._set_ui_processing_state(False)
        self.main_window.ui_components.status_label.setText("Operation cancelled")
        self.main_window.ui_components.progress.setValue(0)

    def _set_ui_processing_state(self, is_processing):
        """Enables or disables UI elements based on processing state."""
        self.main_window.ui_components.extract_btn.setEnabled(not is_processing)
        self.main_window.ui_components.cancel_btn.setVisible(is_processing)
        self.main_window.ui_components.progress.setVisible(is_processing)
        if not is_processing:
            self.main_window.ui_components.progress.setValue(0)

    def _on_closing(self):
        """Saves the application state before quitting."""
        current_tab_widget = self.get_active_tab()
        active_tab_id = next((tid for tid, twidget in self.tabs.items() if twidget == current_tab_widget), None)

        open_tabs_state = []
        for tab_id, tab_widget in self.tabs.items():
            state = tab_widget.get_state()
            state['id'] = tab_id
            open_tabs_state.append(state)

        app_state = {
            "open_tabs": open_tabs_state[-10:],
            "active_tab_id": active_tab_id,
            "window_geometry": {
                "size": [self.main_window.width(), self.main_window.height()],
                "pos": [self.main_window.x(), self.main_window.y()],
            },
        }
        self.config_manager.save_app_state(app_state)
        self.processor_thread.quit()
        self.processor_thread.wait()