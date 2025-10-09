from PySide6.QtCore import QObject, Signal, QThread
from pathlib import Path
import threading
from typing import Dict, Any, Optional

from . import core

class FileProcessorWorker(QObject):
    """
    Worker object that runs in a separate thread and performs the file processing.
    Emits signals to communicate with the main UI thread.
    """
    progress = Signal(int, str)
    complete = Signal(str, str, int)
    error = Signal(str)
    cancelled = Signal()

    def __init__(self, params: Dict[str, Any]):
        super().__init__()
        self.params = params
        self.cancel_event = threading.Event()

    def run(self):
        """Main worker method."""
        try:
            def progress_callback(value: float, status: str):
                self.progress.emit(int(value), status)

            processed_count = core.generate_report_to_file(
                output_file=self.params["output"],
                source_path_str=self.params["source"],
                include_mode=self.params["include_mode"],
                manual_selections_str=self.params["manual_selections"],
                include_patterns=self.params["include_patterns"],
                exclude_patterns=self.params["exclude_patterns"],
                filenames_only=self.params["filenames_only"],
                show_excluded=self.params["show_excluded"],
                cancel_event=self.cancel_event,
                progress_callback=progress_callback,
            )

            if self.cancel_event.is_set():
                self.cancelled.emit()
            else:
                self.complete.emit(
                    "Extraction Complete",
                    f"Extraction finished.\n\n{processed_count} files matched the filters and were saved to:\n{self.params['output']}",
                    processed_count,
                )

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error.emit(f"An unexpected error occurred:\n{e}")

    def cancel(self):
        """Signal the worker to cancel processing."""
        self.cancel_event.set()


class ThreadedFileProcessor:
    """
    Manages the file processing thread and its communication with the UI.
    """
    def __init__(self, app_instance):
        self.app = app_instance
        self.thread: Optional[QThread] = None
        self.worker: Optional[FileProcessorWorker] = None
        self.is_processing = False

    def process_files(self) -> None:
        """Starts file processing in a separate thread."""
        if self.is_processing:
            QMessageBox.warning(self.app, "Processing", "File processing is already in progress.")
            return

        active_tab = self.app.get_active_tab()
        if not active_tab:
            QMessageBox.critical(self.app, "Error", "No active tab found.")
            return

        # Gather all parameters from the UI
        params = self.app.get_processing_parameters()
        if not params["source"] or not params["output"]:
            QMessageBox.critical(self.app, "Error", "Please select a source directory and an output file.")
            return

        self.is_processing = True
        self.app.set_ui_processing_state(True)

        # self.app.config_manager.save_app_state()

        self.thread = QThread()
        self.worker = FileProcessorWorker(params)
        self.worker.moveToThread(self.thread)

        # Connect signals from worker to slots in the main window
        self.worker.progress.connect(self.app.update_progress)
        self.worker.complete.connect(self.app.on_processing_complete)
        self.worker.error.connect(self.app.on_processing_error)
        self.worker.cancelled.connect(self.app.on_processing_cancelled)

        # Connect thread lifecycle signals
        self.thread.started.connect(self.worker.run)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.complete.connect(self.thread.quit)
        self.worker.error.connect(self.thread.quit)
        self.worker.cancelled.connect(self.thread.quit)

        self.thread.start()

    def cancel_processing(self) -> None:
        """Requests cancellation of the processing thread."""
        if self.worker:
            self.worker.cancel()
