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

    def should_process_path(self, path, selected_paths_set):
        """
        Determines if a given path should be processed based on user selections.
        This is a more optimized version.

        Args:
            path (Path): The path to check.
            selected_paths_set (set): A pre-computed set of explicitly checked paths.

        Returns:
            bool: True if the path should be processed, False otherwise.
        """
        path_str = str(path)

        # Check direct selection or if a parent directory was selected
        if any(path_str.startswith(p) for p in selected_paths_set):
            is_selected = True
        else:
            is_selected = False

        # Return based on include/exclude mode
        return is_selected if self.app.include_mode.get() else not is_selected

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
            self.app.status_label["text"] = "Gathering files..."
            self.app.root.update()

            source_path = Path(source)
            all_paths = list(source_path.rglob("*"))

            # Create a set of selected paths for faster lookups
            selected_paths = {
                path_str
                for path_str, item in self.app.tree_view_manager.tree_items.items()
                if item.checked.get()
            }

            # Filter files and directories based on selection
            files_to_process = [
                p
                for p in all_paths
                if p.is_file() and self.should_process_path(p, selected_paths)
            ]

            # Dirs are needed for the structure, even if empty
            dirs_in_structure = {p.parent for p in files_to_process}
            for p in all_paths:
                if p.is_dir() and self.should_process_path(p, selected_paths):
                    dirs_in_structure.add(p)

            total_files = len(files_to_process)

            if total_files == 0 and not dirs_in_structure:
                Messagebox.show_info(
                    "Info", "No files or directories to process with current selection."
                )
                self.app.status_label["text"] = "Ready"
                return

            with open(output, "w", encoding="utf-8", errors="ignore") as f:
                self.write_report_header(f)
                self.write_project_structure_ascii(
                    f, source_path, files_to_process, dirs_in_structure
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
        The format is changed slightly to be more LLM-friendly.
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
            while parent != source_path.parent and parent != source_path:
                paths_in_tree.add(parent)
                parent = parent.parent
        paths_in_tree.add(source_path)

        def build_tree(current_path, prefix=""):
            # Get children of the current path that are part of the structure
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

                # Write file or directory entry
                f.write(f"{prefix}{connector}{child.name}\n")

                # If it's a directory, recurse
                if child.is_dir():
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    build_tree(child, new_prefix)

        # Start building the tree from the root
        f.write(f"{source_path.name}\n")
        build_tree(source_path)
        f.write("\n")

    def write_file_contents(self, f, files_to_process, source, total_files):
        """
        Writes the contents of each processed file to the report.
        """
        f.write("### File Contents\n\n")

        for i, path in enumerate(files_to_process):
            try:
                rel_path = path.relative_to(source)
                f.write(f"--- file: {rel_path} ---\n")

                try:
                    # Read content, ensuring it ends with a newline
                    content = path.read_text(encoding="utf-8", errors="ignore")
                    f.write(content.strip() + "\n")
                except UnicodeDecodeError:
                    f.write("[Binary file - content not displayed]\n")
                except Exception as read_error:
                    f.write(f"[Error reading file: {read_error}]\n")

                f.write("---\n\n")  # End of file marker

                # Update progress bar less frequently to improve performance
                if (i + 1) % 10 == 0 or (i + 1) == total_files:
                    progress = ((i + 1) / total_files) * 100
                    self.app.progress["value"] = progress
                    self.app.status_label["text"] = (
                        f"Processing {i + 1}/{total_files}..."
                    )
                    self.app.root.update_idletasks()

            except Exception as e:
                f.write(f"--- file: {path.name} ---\n")
                f.write(f"[Error processing file path: {e}]\n")
                f.write("---\n\n")
