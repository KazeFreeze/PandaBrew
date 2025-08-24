import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttkb
from ttkbootstrap.dialogs import Messagebox
from pathlib import Path
import threading
import queue
from typing import Dict, Any, Optional

from . import core

class ThreadedFileProcessor:
    """
    Handles file processing in a separate thread to prevent UI freezing.
    Acts as a bridge between the UI and the core processing logic.
    """

    def __init__(self, app_instance):
        """Initializes the threaded file processor."""
        self.app = app_instance
        self.processing_thread: Optional[threading.Thread] = None
        self.cancel_event = threading.Event()
        self.progress_queue = queue.Queue()
        self.is_processing = False

        self._check_progress_queue()

    def _check_progress_queue(self):
        """Periodically checks for progress updates from the worker thread."""
        try:
            while True:
                message = self.progress_queue.get_nowait()
                self._handle_progress_message(message)
        except queue.Empty:
            pass  # No new messages
        finally:
            self.app.root.after(100, self._check_progress_queue)

    def _handle_progress_message(self, message: Dict[str, Any]):
        """Handles progress messages from the worker thread in the main UI thread."""
        msg_type = message.get("type")

        if msg_type == "progress":
            if self.app.progress:
                self.app.progress["value"] = message["value"]
            if self.app.status_label:
                self.app.status_label["text"] = message["status"]
        elif msg_type == "complete":
            self.is_processing = False
            self.app.set_ui_processing_state(False)
            if self.app.progress:
                self.app.progress["value"] = 100
            if self.app.status_label:
                self.app.status_label["text"] = message["status"]
            self._show_success_dialog(message["title"], message["message"])
        elif msg_type == "error":
            self.is_processing = False
            self.app.set_ui_processing_state(False)
            if self.app.status_label:
                self.app.status_label["text"] = "Error occurred"
            Messagebox.show_error("Error", message["message"], parent=self.app.root)
        elif msg_type == "cancelled":
            self.is_processing = False
            self.app.set_ui_processing_state(False)
            if self.app.status_label:
                self.app.status_label["text"] = "Operation cancelled"
            if self.app.progress:
                self.app.progress["value"] = 0

    def process_files(self) -> None:
        """Starts file processing in a separate thread."""
        if self.is_processing:
            Messagebox.show_warning("Processing", "File processing is already in progress.", parent=self.app.root)
            return

        active_tab = self.app.get_active_tab()
        if not active_tab:
            Messagebox.show_error("Error", "No active tab found.", parent=self.app.root)
            return

        source = active_tab["source_path"].get()
        output = active_tab["output_path"].get()

        if not source or not output:
            Messagebox.show_error("Error", "Please select a source directory and an output file.", parent=self.app.root)
            return

        # Save the current state (including global filters) before starting
        self.app.config_manager.save_app_state()

        self.cancel_event.clear()
        self.is_processing = True
        self.app.set_ui_processing_state(True)

        self.processing_thread = threading.Thread(
            target=self._process_files_worker,
            args=(active_tab, source, output),
            daemon=True,
        )
        self.processing_thread.start()

    def cancel_processing(self) -> None:
        """Sets the event to signal cancellation to the worker thread."""
        if self.is_processing:
            self.cancel_event.set()

    def _process_files_worker(self, active_tab: Dict[str, Any], source: str, output: str):
        """
        Worker method that gathers UI data and calls the core processing function.
        """
        try:
            # 1. Gather all necessary data from the UI state
            tree_manager = active_tab["tree_view_manager"]
            manual_selections = tree_manager.checked_paths.copy()
            include_mode = self.app.include_mode.get()
            filenames_only = self.app.filenames_only.get()
            show_excluded = self.app.show_excluded_in_structure.get()

            def get_patterns(widget):
                if not widget:
                    return []
                text = widget.get("1.0", tk.END)
                return [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith('#')]

            global_includes = get_patterns(self.app.global_include_patterns)
            global_excludes = get_patterns(self.app.global_exclude_patterns)

            # 2. Define the progress callback to queue UI updates
            def progress_callback(value: float, status: str):
                self.progress_queue.put({"type": "progress", "value": value, "status": status})

            # 3. Call the core function
            processed_count = core.generate_report_to_file(
                output_file=output,
                source_path_str=source,
                include_mode=include_mode,
                manual_selections_str=manual_selections,
                global_include_patterns=global_includes,
                global_exclude_patterns=global_excludes,
                filenames_only=filenames_only,
                show_excluded=show_excluded,
                cancel_event=self.cancel_event,
                progress_callback=progress_callback,
            )

            # 4. Handle completion or cancellation
            if self.cancel_event.is_set():
                self.progress_queue.put({"type": "cancelled"})
            else:
                self.progress_queue.put({
                    "type": "complete",
                    "title": "Extraction Complete",
                    "message": f"Extraction finished.\n\n{processed_count} files matched the filters and were saved to:\n{output}",
                    "status": f"Complete. {processed_count} files processed.",
                })

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.progress_queue.put({"type": "error", "message": f"An unexpected error occurred:\n{e}"})

    def _show_success_dialog(self, title: str, message: str):
        """Shows a success dialog centered on the main window."""
        Messagebox.show_info(title, message, parent=self.app.root)
