import threading
from PySide6.QtCore import QObject, Signal, Slot
from typing import Dict, Any, List, Set

from . import core

class FileProcessorSignals(QObject):
    """Defines the signals available from the file processing thread."""
    progress = Signal(int, str)  # Percentage, Status message
    complete = Signal(str, str, int)  # Title, Message, Processed count
    error = Signal(str)  # Error message
    cancelled = Signal()

class ThreadedFileProcessor(QObject):
    """
    Handles file processing in a separate thread, communicating with the UI via signals.
    """
    def __init__(self):
        super().__init__()
        self.signals = FileProcessorSignals()
        self.cancel_event = threading.Event()
        self.is_processing = False

    @Slot()
    def process_files(self, process_params: Dict[str, Any]):
        """
        Starts the file processing operation. This slot is designed to be called
        when the processor is moved to a QThread.
        """
        if self.is_processing:
            self.signals.error.emit("Processing is already in progress.")
            return

        self.cancel_event.clear()
        self.is_processing = True

        try:
            def progress_callback(value: float, status: str):
                if self.cancel_event.is_set():
                    # Stop further progress updates if cancellation is requested
                    raise InterruptedError("Processing was cancelled.")
                self.signals.progress.emit(int(value), status)

            processed_count = core.generate_report_to_file(
                output_file=process_params["output_path"],
                source_path_str=process_params["source_path"],
                include_mode=process_params["include_mode"],
                manual_selections_str=process_params["manual_selections"],
                include_patterns=process_params["include_patterns"],
                exclude_patterns=process_params["exclude_patterns"],
                filenames_only=process_params["filenames_only"],
                show_excluded=process_params["show_excluded"],
                cancel_event=self.cancel_event,
                progress_callback=progress_callback,
            )

            if self.cancel_event.is_set():
                self.signals.cancelled.emit()
            else:
                title = "Extraction Complete"
                message = (
                    f"Extraction finished.\n\n{processed_count} files matched the filters "
                    f"and were saved to:\n{process_params['output_path']}"
                )
                self.signals.complete.emit(title, message, processed_count)

        except InterruptedError:
             self.signals.cancelled.emit()
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.signals.error.emit(f"An unexpected error occurred:\n{e}")
        finally:
            self.is_processing = False

    def cancel_processing(self):
        """Signals the worker thread to cancel the operation."""
        if self.is_processing:
            self.cancel_event.set()