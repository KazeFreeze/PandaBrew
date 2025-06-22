import tkinter as tk
from ttkbootstrap.dialogs import Messagebox
from pathlib import Path
import datetime
from utils.helpers import format_file_size
from typing import Set, List


class FileProcessor:
    """
    Handles the logic for processing the selected files and directories
    from the active tab and generating the final output file.
    """

    def __init__(self, app_instance):
        self.app = app_instance

    def should_process_path(
        self, path: Path, selected_paths_set: Set[str], include_mode: bool
    ) -> bool:
        """
        Determines if a given path should be processed based on the user's
        selections and the include/exclude mode.

        A path is "selected" if it or any of its parent directories are in the
        `selected_paths_set`. The function's return value depends on whether the
        application is in include or exclude mode.
        """
        path_str = str(path)
        # A path is considered "selected" if it's in the set, or one of its parent directories is in the set.
        is_selected = any(
            path_str == p or path_str.startswith(str(Path(p) / ""))
            for p in selected_paths_set
        )
        # The result depends on whether we are in "include" or "exclude" mode.
        return is_selected if include_mode else not is_selected

    def show_centered_success_dialog(self, title: str, message: str) -> None:
        """
        Shows a success dialog centered on the main window.
        """
        # Create a custom dialog window
        dialog = tk.Toplevel(self.app.root)
        dialog.title(title)
        dialog.transient(self.app.root)
        dialog.grab_set()
        
        # Make it modal and center it
        dialog.resizable(False, False)
        
        # Set up the dialog content
        main_frame = tk.Frame(dialog, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # Add the message
        message_label = tk.Label(
            main_frame, 
            text=message, 
            justify="left",
            font=("Segoe UI", 9),
            wraplength=400
        )
        message_label.pack(pady=(0, 20))
        
        # Add OK button
        ok_button = tk.Button(
            main_frame,
            text="OK",
            command=dialog.destroy,
            font=("Segoe UI", 9),
            padx=20,
            pady=5
        )
        ok_button.pack()
        ok_button.focus_set()
        
        # Bind Enter key to close dialog
        dialog.bind('<Return>', lambda e: dialog.destroy())
        dialog.bind('<Escape>', lambda e: dialog.destroy())
        
        # Update the dialog to get its size
        dialog.update_idletasks()
        
        # Calculate position to center on parent window
        parent_x = self.app.root.winfo_x()
        parent_y = self.app.root.winfo_y()
        parent_width = self.app.root.winfo_width()
        parent_height = self.app.root.winfo_height()
        
        dialog_width = dialog.winfo_reqwidth()
        dialog_height = dialog.winfo_reqheight()
        
        pos_x = parent_x + (parent_width // 2) - (dialog_width // 2)
        pos_y = parent_y + (parent_height // 2) - (dialog_height // 2)
        
        dialog.geometry(f"{dialog_width}x{dialog_height}+{pos_x}+{pos_y}")

    def process_files(self) -> None:
        """
        Gathers all selected files, generates the project structure and content,
        and writes it to the specified output file.
        """
        active_tab = self.app.get_active_tab()
        if not active_tab:
            Messagebox.show_error("Error", "No active tab found.", parent=self.app.root)
            return

        source = active_tab["source_path"].get()
        output = self.app.output_path.get()
        tree_manager = active_tab["tree_view_manager"]

        if not source or not output:
            Messagebox.show_error(
                "Error",
                "Please select a source directory and an output file.",
                parent=self.app.root,
            )
            return

        try:
            self.app.progress["value"] = 0
            self.app.status_label["text"] = "Gathering files..."
            self.app.root.update_idletasks()

            source_path = Path(source)
            selected_paths = tree_manager.checked_paths
            include_mode = self.app.include_mode.get()

            all_paths_in_dir_list = list(source_path.rglob("*"))

            # Filter files whose content will be written to the output.
            files_to_process = [
                p
                for p in all_paths_in_dir_list
                if p.is_file()
                and self.should_process_path(p, selected_paths, include_mode)
            ]

            # --- Determine all paths that should be rendered in the ASCII tree ---
            # Start with all files that will be processed.
            paths_for_structure = set(files_to_process)

            # Add all parent directories of the files being processed.
            for p in files_to_process:
                parent = p.parent
                while parent.is_relative_to(source_path) and parent != source_path:
                    paths_for_structure.add(parent)
                    parent = parent.parent
            paths_for_structure.add(source_path)

            # Add any directories that were explicitly selected/deselected to the tree.
            for p_str in selected_paths:
                p = Path(p_str)
                if p.exists() and p.is_dir():
                    paths_for_structure.add(p)

            # Finally, for any directory in our structure, add all its immediate children.
            # This ensures that we can see and mark excluded siblings.
            final_paths_for_structure = set(paths_for_structure)
            for p in paths_for_structure:
                if p.is_dir():
                    try:
                        for child in p.iterdir():
                            final_paths_for_structure.add(child)
                    except (IOError, PermissionError):
                        continue

            total_files = len(files_to_process)
            if total_files == 0 and not any(
                self.should_process_path(p, selected_paths, include_mode)
                for p in final_paths_for_structure
                if p.is_dir()
            ):
                Messagebox.show_info(
                    "Info",
                    "No files or directories match the current selection.",
                    parent=self.app.root,
                )
                self.app.status_label["text"] = "Ready"
                return

            # Write the final report
            with open(output, "w", encoding="utf-8", errors="ignore") as f:
                self.write_report_header(f)
                self.write_project_structure_ascii(
                    f,
                    source_path,
                    final_paths_for_structure,
                    selected_paths,
                    include_mode,
                )
                if not self.app.filenames_only.get():
                    self.write_file_contents(
                        f, files_to_process, source_path, total_files
                    )

            self.app.progress["value"] = 100
            self.app.status_label["text"] = (
                f"Extraction complete. {total_files} files processed."
            )
            
            # Use the custom centered success dialog
            success_message = f"Extraction Complete\n\n{total_files} files processed.\n\nOutput saved to:\n{output}"
            self.show_centered_success_dialog("Success", success_message)

        except Exception as e:
            self.app.status_label["text"] = "Error occurred"
            Messagebox.show_error(
                "Error",
                f"An error occurred during extraction:\n{str(e)}",
                parent=self.app.root,
            )
            import traceback

            traceback.print_exc()

    def write_report_header(self, f) -> None:
        """Writes the header for the output file."""
        mode = "INCLUDE" if self.app.include_mode.get() else "EXCLUDE"
        f.write(f"--- Project Extraction Report ---\n")
        f.write(f"Timestamp: {datetime.datetime.now().isoformat()}\n")
        f.write(f"Selection Mode: {mode} checked items\n")
        f.write("---\n\n")

    def write_project_structure_ascii(
        self,
        f,
        source_path: Path,
        paths_for_structure: Set[Path],
        selected_paths: Set[str],
        include_mode: bool,
    ) -> None:
        """
        Writes a classic ASCII tree structure to the output file.
        FIX: Now marks any excluded file or directory and does not recurse into excluded directories.
        """
        f.write("### Project Structure\n\n")

        # Add all parent directories to ensure the tree is complete.
        for p in list(paths_for_structure):
            parent = p.parent
            try:
                while parent.relative_to(source_path):
                    if parent == source_path:
                        break
                    paths_for_structure.add(parent)
                    parent = parent.parent
            except ValueError:
                continue
        paths_for_structure.add(source_path)

        def build_tree(current_path, prefix=""):
            try:
                # Render children that are in our pre-calculated set of paths to show.
                children = sorted(
                    [p for p in current_path.iterdir() if p in paths_for_structure],
                    key=lambda p: (p.is_file(), p.name.lower()),
                )
            except (IOError, PermissionError):
                children = []

            for i, child in enumerate(children):
                is_last = i == len(children) - 1
                connector = "└── " if is_last else "├── "
                f.write(f"{prefix}{connector}{child.name}")

                is_processed = self.should_process_path(
                    child, selected_paths, include_mode
                )

                if not is_processed:
                    f.write(" [EXCLUDED]\n")
                    # If a directory is excluded, do not show its children.
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

    def write_file_contents(
        self, f, files_to_process: List[Path], source_path: Path, total_files: int
    ) -> None:
        """Writes the contents of each processed file to the output."""
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

                if (i + 1) % 10 == 0 or (i + 1) == total_files:
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