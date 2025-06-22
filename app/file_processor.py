import tkinter as tk
from ttkbootstrap.dialogs import Messagebox
from pathlib import Path
import datetime
from utils.helpers import format_file_size


class FileProcessor:
    """
    Handles the logic for processing the selected files and directories,
    and generating the final output file.
    """

    def __init__(self, app_instance):
        """
        Initializes the FileProcessor.
        """
        self.app = app_instance

    def should_process_path(self, path):
        """
        Determines if a given path should be processed based on the user's selections and the include/exclude mode.
        """
        path_str = str(path)

        # Check direct selection
        if path_str in self.app.tree_view_manager.tree_items:
            if self.app.tree_view_manager.tree_items[path_str].checked.get():
                return self.app.include_mode.get()

        # Check parent selection
        for parent_path_str, tree_item in self.app.tree_view_manager.tree_items.items():
            if path_str.startswith(parent_path_str) and path_str != parent_path_str:
                if tree_item.checked.get():
                    return self.app.include_mode.get()

        return not self.app.include_mode.get()

    def process_files(self):
        """
        Main method to start the file processing.
        It gathers the files, generates the output report, and updates the UI with progress.
        """
        source = self.app.source_path.get()
        output = self.app.output_path.get()

        if not source or not output:
            Messagebox.show_error(
                "Error", "Please select both source directory and output file"
            )
            return

        try:
            self.app.progress["value"] = 0
            self.app.status_label["text"] = "Processing..."
            self.app.root.update()

            all_paths = list(Path(source).rglob("*"))

            files_to_process = [
                p for p in all_paths if p.is_file() and self.should_process_path(p)
            ]
            dirs_to_process = [
                p for p in all_paths if p.is_dir() and self.should_process_path(p)
            ]

            total_files = len(files_to_process)

            if total_files == 0 and not any(dirs_to_process):
                Messagebox.show_info(
                    "Info", "No files or directories to process with current selection."
                )
                self.app.status_label["text"] = "Ready"
                return

            with open(output, "w", encoding="utf-8") as f:
                self.write_report_header(f)
                self.write_project_structure(
                    f, Path(source), files_to_process, dirs_to_process
                )
                if not self.app.filenames_only.get():
                    self.write_file_contents(f, files_to_process, source, total_files)

            self.app.progress["value"] = 100
            self.app.status_label["text"] = f"Complete! Processed {total_files} files"
            self.app.config_manager.save_config()
            Messagebox.show_info(
                "Success",
                f"Extraction complete!\n\nProcessed {total_files} files\nSaved to: {output}",
            )

        except Exception as e:
            self.app.status_label["text"] = "Error occurred"
            Messagebox.show_error("Error", f"Error during extraction:\n{str(e)}")

    def write_report_header(self, f):
        """
        Writes the header section of the output report.
        """
        checked_status = "checked" if self.app.include_mode.get() else "unchecked"
        f.write(f"# Project Extract (-{checked_status})\n\n")

    def write_project_structure(
        self, f, source_path, files_to_process, dirs_to_process
    ):
        """
        Writes the project structure tree to the output file using the specified format.
        """
        f.write("# Structure\n")

        paths_in_structure = set()

        # Add the root source directory
        paths_in_structure.add(source_path)

        # Add all files to be processed and their parents
        for p in files_to_process:
            paths_in_structure.add(p)
            for parent in p.parents:
                if parent == source_path:
                    break
                paths_in_structure.add(parent)

        # Add all directories to be processed and their parents
        for p in dirs_to_process:
            paths_in_structure.add(p)
            for parent in p.parents:
                if parent == source_path:
                    break
                paths_in_structure.add(parent)

        def build_tree(path, level=0):
            # Only process paths that should be in the structure
            if path not in paths_in_structure and path != source_path:
                return

            prefix = "> " * level
            if path.is_dir():
                f.write(f"{prefix}> {path.name}\n")
                try:
                    # Sort children: directories first, then files, alphabetically
                    children = sorted(
                        path.iterdir(), key=lambda p: (p.is_file(), p.name.lower())
                    )
                    for child in children:
                        # Recursive call for children that should be in the structure
                        if child in paths_in_structure:
                            build_tree(child, level + 1)
                except PermissionError:
                    f.write(f"{prefix}  - [Permission Denied]\n")
            elif path.is_file():
                f.write(f"{prefix}- {path.name}\n")

        # Start building the tree from the source path
        f.write(f"> {source_path.name}\n")
        children = sorted(
            source_path.iterdir(), key=lambda p: (p.is_file(), p.name.lower())
        )
        for child in children:
            if child in paths_in_structure:
                build_tree(child, level=1)
        f.write("\n")

    def write_file_contents(self, f, files_to_process, source, total_files):
        """
        Writes the contents of each processed file to the report.
        """
        f.write("# Contents\n\n")

        for i, path in enumerate(files_to_process):
            try:
                rel_path = path.relative_to(source)
                f.write(f"@ {rel_path}\n")

                try:
                    # Read content without adding markdown code fences
                    content = path.read_text(encoding="utf-8")
                    f.write(content.rstrip() + "\n\n")
                except UnicodeDecodeError:
                    f.write("[Binary file - content not displayed]\n\n")
                except Exception as read_error:
                    f.write(f"[Error reading file: {read_error}]\n\n")

                progress = ((i + 1) / total_files) * 100
                self.app.progress["value"] = progress
                self.app.status_label["text"] = f"Processing {i + 1}/{total_files}..."
                self.app.root.update()

            except Exception as e:
                f.write(f"[Error processing file path: {e}]\n\n")
