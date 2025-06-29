import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttkb
from ttkbootstrap.dialogs import Messagebox
from pathlib import Path
import datetime
import threading
import queue
from typing import Set, List, Dict, Any, Optional

from utils.helpers import format_file_size

# Define consistent fonts for the terminal theme
TERMINAL_FONT = ("Cascadia Code", 9)


class ThreadedFileProcessor:
    """
    Handles file processing in a separate thread to prevent UI freezing.
    Uses a queue-based communication system for thread-safe UI updates.
    """

    def __init__(self, app_instance):
        """Initializes the threaded file processor."""
        self.app = app_instance
        self.processing_thread: Optional[threading.Thread] = None
        self.cancel_event = threading.Event()
        self.progress_queue = queue.Queue()
        self.is_processing = False

        # Start the UI update checker
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
            # Schedule the next check
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
            if self.app.progress:
                self.app.progress["value"] = 100
            if self.app.status_label:
                self.app.status_label["text"] = message["status"]
            self.is_processing = False
            self.app.set_ui_processing_state(False)
            self._show_success_dialog(message["title"], message["message"])

        elif msg_type == "error":
            if self.app.status_label:
                self.app.status_label["text"] = "Error occurred"
            self.is_processing = False
            self.app.set_ui_processing_state(False)
            Messagebox.show_error("Error", message["message"], parent=self.app.root)

        elif msg_type == "cancelled":
            if self.app.status_label:
                self.app.status_label["text"] = "Operation cancelled"
            if self.app.progress:
                self.app.progress["value"] = 0
            self.is_processing = False
            self.app.set_ui_processing_state(False)

    def process_files(self) -> None:
        """Starts file processing in a separate thread."""
        if self.is_processing:
            Messagebox.show_warning(
                "Processing",
                "File processing is already in progress.",
                parent=self.app.root,
            )
            return

        active_tab = self.app.get_active_tab()
        if not active_tab:
            Messagebox.show_error("Error", "No active tab found.", parent=self.app.root)
            return

        source = active_tab["source_path"].get()
        output = active_tab["output_path"].get()

        if not source or not output:
            Messagebox.show_error(
                "Error",
                "Please select a source directory and an output file for the current tab.",
                parent=self.app.root,
            )
            return

        # Reset cancellation flag and set UI state
        self.cancel_event.clear()
        self.is_processing = True
        self.app.set_ui_processing_state(True)

        # Start processing in a separate thread
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

    def _process_files_worker(
        self, active_tab: Dict[str, Any], source: str, output: str
    ):
        """
        Worker method that runs in a separate thread.
        It performs the file operations and communicates with the UI thread via queue messages.
        """
        try:
            self.progress_queue.put(
                {"type": "progress", "value": 0, "status": "Gathering files..."}
            )

            source_path = Path(source)
            tree_manager = active_tab["tree_view_manager"]
            selected_paths = tree_manager.checked_paths.copy()  # Thread-safe copy
            include_mode = self.app.include_mode.get()

            # Check for early cancellation
            if self.cancel_event.is_set():
                self.progress_queue.put({"type": "cancelled"})
                return

            all_paths_in_dir_list = list(source_path.rglob("*"))

            # Filter files to be processed
            files_to_process = []
            total_paths = len(all_paths_in_dir_list)
            for i, p in enumerate(all_paths_in_dir_list):
                if self.cancel_event.is_set():
                    self.progress_queue.put({"type": "cancelled"})
                    return

                if p.is_file() and self._should_process_path(
                    p, selected_paths, include_mode, source_path
                ):
                    files_to_process.append(p)

                if i % 100 == 0:
                    progress = (i / total_paths) * 20
                    self.progress_queue.put(
                        {
                            "type": "progress",
                            "value": progress,
                            "status": f"Filtering files... ({i}/{total_paths})",
                        }
                    )

            paths_for_structure = self._build_structure_paths(
                files_to_process, selected_paths, source_path
            )

            total_files = len(files_to_process)
            if total_files == 0:
                self.progress_queue.put(
                    {
                        "type": "complete",
                        "title": "No Files",
                        "message": "No files match the current selection.",
                        "status": "No files to process",
                    }
                )
                return

            self._write_report_threaded(
                output,
                source_path,
                paths_for_structure,
                selected_paths,
                include_mode,
                files_to_process,
                total_files,
            )

        except Exception as e:
            import traceback

            traceback.print_exc()
            self.progress_queue.put(
                {
                    "type": "error",
                    "message": f"An error occurred during extraction:\n{str(e)}",
                }
            )

    def _write_report_threaded(
        self,
        output: str,
        source_path: Path,
        paths_for_structure: Set[Path],
        selected_paths: Set[str],
        include_mode: bool,
        files_to_process: List[Path],
        total_files: int,
    ):
        """Writes the final report with cancellation checks and progress updates."""
        try:
            with open(output, "w", encoding="utf-8", errors="ignore") as f:
                self._write_report_header(f, include_mode)

                self.progress_queue.put(
                    {
                        "type": "progress",
                        "value": 25,
                        "status": "Writing project structure...",
                    }
                )
                if self.cancel_event.is_set():
                    self.progress_queue.put({"type": "cancelled"})
                    return

                self._write_project_structure_ascii(
                    f, source_path, paths_for_structure, selected_paths, include_mode
                )

                if not self.app.filenames_only.get():
                    self._write_file_contents_threaded(
                        f, files_to_process, source_path, total_files
                    )

            if self.cancel_event.is_set():
                return

            self.progress_queue.put(
                {
                    "type": "complete",
                    "title": "Success",
                    "message": f"Extraction Complete\n\n{total_files} files processed.\n\nOutput saved to:\n{output}",
                    "status": f"Extraction complete. {total_files} files processed.",
                }
            )
        except IOError as e:
            self.progress_queue.put(
                {
                    "type": "error",
                    "message": f"Could not write to output file:\n{output}\n\nError: {e}",
                }
            )

    def _write_file_contents_threaded(
        self,
        f,
        files_to_process: List[Path],
        source_path: Path,
        total_files: int,
    ):
        """Writes file contents with cancellation checks and progress updates."""
        f.write("### File Contents\n\n")

        for i, path in enumerate(files_to_process):
            if self.cancel_event.is_set():
                return

            try:
                current_file_num = i + 1
                rel_path = path.relative_to(source_path)

                base_progress = 25
                file_progress = (i / total_files) * 75
                total_progress = base_progress + file_progress

                self.progress_queue.put(
                    {
                        "type": "progress",
                        "value": total_progress,
                        "status": f"Processing {current_file_num}/{total_files}: {rel_path.name}",
                    }
                )

                f.write(f"--- file: {rel_path} ---\n")
                try:
                    content = path.read_text(encoding="utf-8", errors="ignore")
                    f.write(content.strip() + "\n")
                except Exception as read_error:
                    f.write(f"[Error reading file: {read_error}]\n")
                f.write("---\n\n")

            except Exception as e:
                f.write(
                    f"--- file: {path.name} ---\n[Error processing file: {e}]\n---\n\n"
                )

    def _should_process_path(
        self,
        path: Path,
        selected_paths_set: Set[str],
        include_mode: bool,
        source_path: Path,
    ) -> bool:
        """
        Determines if a given path should be processed based on the selection mode.
        This has been rewritten for clarity and to fix bugs with exclusion logic.
        """
        path_str = str(path)

        if include_mode:
            # INCLUDE MODE: Process if the path or any of its ancestors are checked.
            return any(
                path_str == p or path_str.startswith(str(Path(p) / ""))
                for p in selected_paths_set
            )
        else:
            # EXCLUDE MODE: Process if the path AND all of its ancestors are UNCHECKED.
            # In other words, exclude if the path or any ancestor is in the checked set.
            current = path
            while True:
                if str(current) in selected_paths_set:
                    return False  # Exclude if the path or a parent is checked

                # Stop if we've reached the source directory itself and it wasn't in the set
                if current == source_path:
                    break

                # Stop if we've reached the top of the filesystem
                if current.parent == current:
                    break

                current = current.parent
            return True  # Include because neither it nor any parent was in the exclude list

    def _build_structure_paths(
        self,
        files_to_process: List[Path],
        selected_paths: Set[str],
        source_path: Path,
    ) -> Set[Path]:
        """Builds the set of all paths that need to be displayed in the ASCII structure tree."""
        paths_for_structure = set(files_to_process)
        for p in files_to_process:
            parent = p.parent
            while parent.is_relative_to(source_path) and parent != source_path:
                paths_for_structure.add(parent)
                parent = parent.parent
        paths_for_structure.add(source_path)

        for p_str in selected_paths:
            p = Path(p_str)
            if p.exists() and p.is_dir():
                paths_for_structure.add(p)

        final_paths = set(paths_for_structure)
        for p in paths_for_structure:
            if p.is_dir():
                try:
                    for child in p.iterdir():
                        final_paths.add(child)
                except (IOError, PermissionError):
                    continue
        return final_paths

    def _write_report_header(self, f, include_mode: bool):
        """Writes the report header."""
        mode = "INCLUDE" if include_mode else "EXCLUDE"
        f.write(f"--- Project Extraction Report ---\n")
        f.write(f"Timestamp: {datetime.datetime.now().isoformat()}\n")
        f.write(f"Selection Mode: {mode} checked items\n")
        f.write("---\n\n")

    def _write_project_structure_ascii(
        self,
        f,
        source_path: Path,
        paths_for_structure: Set[Path],
        selected_paths: Set[str],
        include_mode: bool,
    ):
        """Writes a classic ASCII tree structure to the output file."""
        f.write("### Project Structure\n\n")

        def build_tree(current_path, prefix=""):
            try:
                children = sorted(
                    list(current_path.iterdir()),
                    key=lambda p: (p.is_file(), p.name.lower()),
                )
            except (IOError, PermissionError):
                children = []

            displayable_children = [p for p in children if p in paths_for_structure]

            for i, child in enumerate(displayable_children):
                is_last = i == len(displayable_children) - 1
                connector = "└── " if is_last else "├── "
                f.write(f"{prefix}{connector}{child.name}")

                is_processed = self._should_process_path(
                    child, selected_paths, include_mode, source_path
                )

                if not is_processed:
                    f.write(" [EXCLUDED]\n")
                    if child.is_dir():
                        continue
                else:
                    f.write("\n")

                if child.is_dir():
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    build_tree(child, new_prefix)

        f.write(f"{source_path.name}\n")
        build_tree(source_path)
        f.write("\n")

    def _show_success_dialog(self, title: str, message: str):
        """Shows success dialog in the main thread."""
        self.app.root.after(
            0, lambda: self._show_centered_success_dialog(title, message)
        )

    def _show_centered_success_dialog(self, title: str, message: str):
        """Shows a success dialog centered on the main window with the new theme."""
        dialog = tk.Toplevel(self.app.root)
        dialog.title(title)
        dialog.configure(bg=self.app.style.colors.get("bg"))
        dialog.transient(self.app.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        main_frame = ttkb.Frame(dialog, padding=20)
        main_frame.pack(fill="both", expand=True)

        message_label = ttkb.Label(
            main_frame,
            text=message,
            justify="left",
            font=TERMINAL_FONT,
            wraplength=400,
        )
        message_label.pack(pady=(0, 20))

        ok_button = ttkb.Button(
            main_frame, text="OK", command=dialog.destroy, bootstyle="success"
        )
        ok_button.pack()
        ok_button.focus_set()

        dialog.bind("<Return>", lambda e: dialog.destroy())
        dialog.bind("<Escape>", lambda e: dialog.destroy())

        dialog.update_idletasks()
        parent_x = self.app.root.winfo_x()
        parent_y = self.app.root.winfo_y()
        parent_width = self.app.root.winfo_width()
        parent_height = self.app.root.winfo_height()
        dialog_width = dialog.winfo_reqwidth()
        dialog_height = dialog.winfo_reqheight()
        pos_x = parent_x + (parent_width // 2) - (dialog_width // 2)
        pos_y = parent_y + (parent_height // 2) - (dialog_height // 2)
        dialog.geometry(f"+{pos_x}+{pos_y}")
