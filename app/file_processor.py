import tkinter as tk
from ttkbootstrap.dialogs import Messagebox
from pathlib import Path
import datetime
from utils.helpers import format_file_size


class FileProcessor:
    """
    Handles the logic for processing the selected files and directories
    from the active tab and generating the final output file.
    """

    def __init__(self, app_instance):
        """
        Initializes the FileProcessor.
        """
        self.app = app_instance

    def should_process_path(self, path, selected_paths_set, include_mode):
        """
        Determines if a given path should be processed based on user selections.
        """
        path_str = str(path)

        # Check if the path or any of its parents are in the selected set
        is_selected = any(
            path_str == p
            or path_str.startswith(p + "\\")
            or path_str.startswith(p + "/")
            for p in selected_paths_set
        )

        # Return based on include/exclude mode
        return is_selected if include_mode else not is_selected

    def process_files(self):
        """
        Main method to start file processing using data from the active tab.
        """
        active_tab = self.app.get_active_tab()
        if not active_tab:
            Messagebox.show_error("Error", "No active tab found.")
            return

        source = active_tab["source_path"].get()
        output = self.app.output_path.get()
        tree_manager = active_tab["tree_view_manager"]

        if not source or not output:
            Messagebox.show_error(
                "Error", "Please select a source directory and an output file."
            )
            return

        try:
            self.app.progress["value"] = 0
            self.app.status_label["text"] = "Gathering files..."
            self.app.root.update_idletasks()

            source_path = Path(source)
            all_paths_in_dir = list(source_path.rglob("*"))

            # Get selections from the active tab's tree manager
            selected_paths = {
                path_str
                for path_str, item in tree_manager.tree_items.items()
                if item.checked.get()
            }

            include_mode = self.app.include_mode.get()

            # Filter files and directories based on selection
            files_to_process = [
                p
                for p in all_paths_in_dir
                if p.is_file()
                and self.should_process_path(p, selected_paths, include_mode)
            ]

            # Dirs are needed for the structure, even if empty, if they were part of the selection logic
            dirs_in_structure = {p.parent for p in files_to_process}
            for p in all_paths_in_dir:
                if p.is_dir() and self.should_process_path(
                    p, selected_paths, include_mode
                ):
                    dirs_in_structure.add(p)

            total_files = len(files_to_process)

            if total_files == 0 and not dirs_in_structure:
                Messagebox.show_info(
                    "Info", "No files or directories match the current selection."
                )
                self.app.status_label["text"] = "Ready"
                return

            with open(output, "w", encoding="utf-8", errors="ignore") as f:
                self.write_report_header(f)
                self.write_project_structure_ascii(
                    f, source_path, files_to_process, dirs_in_structure
                )
                if not self.app.filenames_only.get():
                    self.write_file_contents(
                        f, files_to_process, source_path, total_files
                    )

            self.app.progress["value"] = 100
            self.app.status_label["text"] = f"Complete! Processed {total_files} files"
            Messagebox.show_info(
                "Success",
                f"Extraction complete!\nProcessed {total_files} files.\nSaved to: {output}",
            )

        except Exception as e:
            self.app.status_label["text"] = "Error occurred"
            Messagebox.show_error(
                "Error", f"An error occurred during extraction:\n{str(e)}"
            )
            import traceback

            traceback.print_exc()

    def write_report_header(self, f):
        """
        Writes the header section of the output report.
        """
        mode = "INCLUDE" if self.app.include_mode.get() else "EXCLUDE"
        f.write(f"--- Project Extraction Report ---\n")
        f.write(f"Timestamp: {datetime.datetime.now().isoformat()}\n")
        f.write(f"Selection Mode: {mode} checked items\n")
        f.write("---\n\n")

    def write_project_structure_ascii(
        self, f, source_path, files_to_process, dirs_in_structure
    ):
        """
        Writes the project structure as a clean ASCII tree.
        """
        f.write("### Project Structure\n\n")

        # Create a set of all paths that should appear in the tree
        paths_in_tree = set(files_to_process) | dirs_in_structure
        # Also include all parent directories of the paths in the tree
        for p in list(paths_in_tree):
            parent = p.parent
            while parent.is_relative_to(source_path) and parent != source_path:
                paths_in_tree.add(parent)
                parent = parent.parent
        paths_in_tree.add(source_path)

        def build_tree(current_path, prefix=""):
            try:
                children = sorted(
                    [p for p in current_path.iterdir() if p in paths_in_tree],
                    key=lambda p: (p.is_file(), p.name.lower()),
                )
            except (IOError, PermissionError):
                children = []

            for i, child in enumerate(children):
                is_last = i == len(children) - 1
                connector = "└── " if is_last else "├── "
                f.write(f"{prefix}{connector}{child.name}\n")
                if child.is_dir():
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    build_tree(child, new_prefix)

        f.write(f"{source_path.name}\n")
        build_tree(source_path)
        f.write("\n")

    def write_file_contents(self, f, files_to_process, source_path, total_files):
        """
        Writes the contents of each processed file to the report.
        """
        f.write("### File Contents\n\n")

        for i, path in enumerate(files_to_process):
            try:
                rel_path = path.relative_to(source_path)
                f.write(f"--- file: {rel_path} ---\n")

                try:
                    content = path.read_text(encoding="utf-8", errors="ignore")
                    f.write(content.strip() + "\n")
                except Exception as read_error:
                    f.write(f"[Error reading file: {read_error}]\n")

                f.write("---\n\n")

                if (i + 1) % 5 == 0 or (i + 1) == total_files:
                    progress = ((i + 1) / total_files) * 100
                    self.app.progress["value"] = progress
                    self.app.status_label["text"] = (
                        f"Processing {i + 1}/{total_files}..."
                    )
                    self.app.root.update_idletasks()

            except Exception as e:
                f.write(
                    f"--- file: {path.name} ---\n[Error processing file path: {e}]\n---\n\n"
                )
