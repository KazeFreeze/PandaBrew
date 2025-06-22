import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import datetime
from utils.helpers import get_file_icon, get_language_for_highlighting, format_file_size


class FileProcessor:
    """
    Handles the logic for processing the selected files and directories,
    and generating the final output file.
    """

    def __init__(self, app_instance):
        """
        Initializes the FileProcessor.

        Args:
            app_instance: An instance of the main application class.
        """
        self.app = app_instance

    def should_process_path(self, path):
        """
        Determines if a given path should be processed based on the user's selections and the include/exclude mode.

        Args:
            path (Path): The path to check.

        Returns:
            bool: True if the path should be processed, False otherwise.
        """
        path_str = str(path)

        if path_str in self.app.tree_view_manager.tree_items:
            if self.app.tree_view_manager.tree_items[path_str].checked.get():
                return self.app.include_mode.get()

        for item_path, tree_item in self.app.tree_view_manager.tree_items.items():
            if (
                path_str.startswith(item_path)
                and item_path != path_str
                and tree_item.checked.get()
            ):
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
            messagebox.showerror(
                "Error", "Please select both source directory and output file"
            )
            return

        try:
            self.app.progress["value"] = 0
            self.app.status_label["text"] = "Processing..."
            self.app.root.update()

            files_to_process = [
                p
                for p in Path(source).rglob("*")
                if p.is_file() and self.should_process_path(p)
            ]
            total_files = len(files_to_process)

            if total_files == 0:
                messagebox.showinfo(
                    "Info", "No files to process with current selection."
                )
                self.app.status_label["text"] = "Ready"
                return

            with open(output, "w", encoding="utf-8") as f:
                self.write_report_header(f, source, total_files)
                self.write_project_structure(f, source)
                if not self.app.filenames_only.get():
                    self.write_file_contents(f, files_to_process, source, total_files)

            self.app.progress["value"] = 100
            self.app.status_label["text"] = (
                f"✅ Complete! Processed {total_files} files"
            )
            self.app.config_manager.save_config()
            messagebox.showinfo(
                "Success",
                f"Extraction complete!\n\nProcessed {total_files} files\nSaved to: {output}",
            )

        except Exception as e:
            self.app.status_label["text"] = "❌ Error occurred"
            messagebox.showerror("Error", f"Error during extraction:\n{str(e)}")

    def write_report_header(self, f, source, total_files):
        """
        Writes the header section of the output report.

        Args:
            f: The file object to write to.
            source (str): The source directory path.
            total_files (int): The total number of files being processed.
        """
        mode_str = "Include" if self.app.include_mode.get() else "Exclude"
        content_type = (
            "Filenames Only" if self.app.filenames_only.get() else "Full Content"
        )
        f.write(f"# 🚀 Code Extraction Report\n")
        f.write(f"**Source:** {source}\n")
        f.write(f"**Mode:** {mode_str} checked items\n")
        f.write(f"**Content:** {content_type}\n")
        f.write(f"**Files Processed:** {total_files}\n")
        f.write(
            f"**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )

    def write_project_structure(self, f, source):
        """
        Writes the project structure tree to the output file.

        Args:
            f: The file object to write to.
            source (str): The source directory path.
        """
        f.write("## 📂 Project Structure\n\n")
        f.write("```\n")

        def write_structure(path, level=0):
            if self.should_process_path(path):
                indent = "  " * level
                if path.is_dir():
                    f.write(f"{indent}📁 {path.name}/\n")
                    try:
                        for child in sorted(
                            path.iterdir(),
                            key=lambda p: (p.is_file(), p.name.lower()),
                        ):
                            write_structure(child, level + 1)
                    except PermissionError:
                        f.write(f"{indent}  🔒 [Permission Denied]\n")
                else:
                    icon = get_file_icon(path)
                    size = ""
                    try:
                        file_size = path.stat().st_size
                        size = f" ({format_file_size(file_size)})"
                    except:
                        pass
                    f.write(f"{indent}{icon} {path.name}{size}\n")

        write_structure(Path(source))
        f.write("```\n\n")

    def write_file_contents(self, f, files_to_process, source, total_files):
        """
        Writes the contents of each processed file to the report.

        Args:
            f: The file object to write to.
            files_to_process (list): A list of Path objects for the files to process.
            source (str): The source directory path.
            total_files (int): The total number of files being processed.
        """
        f.write("## 📄 File Contents\n\n")

        for i, path in enumerate(files_to_process):
            try:
                rel_path = path.relative_to(source)
                icon = get_file_icon(path)
                f.write(f"### {icon} `{rel_path}`\n\n")

                try:
                    content = path.read_text(encoding="utf-8")
                    lang = get_language_for_highlighting(path.suffix)
                    f.write(f"```{lang}\n")
                    f.write(content.rstrip() + "\n")
                    f.write("```\n\n")
                except UnicodeDecodeError:
                    f.write("```\n[Binary file - content not displayed]\n```\n\n")

                progress = ((i + 1) / total_files) * 100
                self.app.progress["value"] = progress
                self.app.status_label["text"] = f"Processing {i + 1}/{total_files}..."
                self.app.root.update()

            except Exception as e:
                f.write(f"```\n[Error reading file: {e}]\n```\n\n")
