import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import os
import json


class TreeItem:
    def __init__(self, path, parent=None):
        self.path = Path(path)
        self.parent = parent
        self.children = []
        self.expanded = False
        self.checked = tk.BooleanVar(value=False)
        self.is_loaded = False
        self.is_file = self.path.is_file()
        # Container will store reference to the frame containing child items
        self.container = None


class CodeExtractorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Code Extractor")
        self.root.geometry("800x600")

        self.tree_items = {}  # Store TreeItem objects
        self.include_mode = tk.BooleanVar(
            value=True
        )  # True = include checked, False = exclude checked

        # Load saved directories
        self.config_file = Path.home() / ".code_extractor_config.json"
        self.load_config()

        self.create_gui()

        # If we have saved paths, set them
        if self.config.get("last_source"):
            self.source_path.set(self.config["last_source"])
            self.refresh_tree()
        if self.config.get("last_output"):
            self.output_path.set(self.config["last_output"])

    def load_config(self):
        try:
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    self.config = json.load(f)
                    # Keep only the last 5 entries
                    for key in ["recent_sources", "recent_outputs"]:
                        if key in self.config:
                            self.config[key] = self.config[key][-5:]
            else:
                self.config = {
                    "last_source": "",
                    "last_output": "",
                    "recent_sources": [],
                    "recent_outputs": [],
                }
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config = {
                "last_source": "",
                "last_output": "",
                "recent_sources": [],
                "recent_outputs": [],
            }

    def save_config(self):
        try:
            # Update last used paths
            self.config["last_source"] = self.source_path.get()
            self.config["last_output"] = self.output_path.get()

            # Update recent lists without duplicates
            if self.source_path.get():
                if "recent_sources" not in self.config:
                    self.config["recent_sources"] = []
                if self.source_path.get() in self.config["recent_sources"]:
                    self.config["recent_sources"].remove(self.source_path.get())
                self.config["recent_sources"].append(self.source_path.get())
                self.config["recent_sources"] = self.config["recent_sources"][
                    -5:
                ]  # Keep last 5

            if self.output_path.get():
                if "recent_outputs" not in self.config:
                    self.config["recent_outputs"] = []
                if self.output_path.get() in self.config["recent_outputs"]:
                    self.config["recent_outputs"].remove(self.output_path.get())
                self.config["recent_outputs"].append(self.output_path.get())
                self.config["recent_outputs"] = self.config["recent_outputs"][
                    -5:
                ]  # Keep last 5

            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def create_gui(self):
        # Top frame for directory selection
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill="x", padx=10, pady=5)

        # Source folder selection
        source_frame = ttk.LabelFrame(top_frame, text="Source Directory", padding=10)
        source_frame.pack(fill="x", pady=5)

        self.source_path = tk.StringVar()
        source_entry = ttk.Entry(source_frame, textvariable=self.source_path, width=70)
        source_entry.pack(side="left", padx=5)

        # Source directory dropdown
        if self.config.get("recent_sources"):
            source_menu = tk.Menu(self.root, tearoff=0)
            for path in reversed(self.config["recent_sources"]):
                source_menu.add_command(
                    label=path,
                    command=lambda p=path: (
                        self.source_path.set(p),
                        self.refresh_tree(),
                    ),
                )

            def show_source_history(event):
                source_menu.post(event.x_root, event.y_root)

            source_entry.bind(
                "<Button-3>", show_source_history
            )  # Right-click for history

        ttk.Button(source_frame, text="Browse", command=self.browse_source).pack(
            side="left"
        )

        # Output file selection
        output_frame = ttk.LabelFrame(top_frame, text="Output File", padding=10)
        output_frame.pack(fill="x", pady=5)

        self.output_path = tk.StringVar()
        output_entry = ttk.Entry(output_frame, textvariable=self.output_path, width=70)
        output_entry.pack(side="left", padx=5)

        # Output file dropdown
        if self.config.get("recent_outputs"):
            output_menu = tk.Menu(self.root, tearoff=0)
            for path in reversed(self.config["recent_outputs"]):
                output_menu.add_command(
                    label=path, command=lambda p=path: self.output_path.set(p)
                )

            def show_output_history(event):
                output_menu.post(event.x_root, event.y_root)

            output_entry.bind(
                "<Button-3>", show_output_history
            )  # Right-click for history

        ttk.Button(output_frame, text="Browse", command=self.browse_output).pack(
            side="left"
        )

        # Mode selection
        mode_frame = ttk.Frame(top_frame)
        mode_frame.pack(fill="x", pady=5)
        ttk.Radiobutton(
            mode_frame,
            text="Include checked items",
            variable=self.include_mode,
            value=True,
        ).pack(side="left", padx=5)
        ttk.Radiobutton(
            mode_frame,
            text="Exclude checked items",
            variable=self.include_mode,
            value=False,
        ).pack(side="left", padx=5)

        # Create tree frame
        tree_frame = ttk.LabelFrame(self.root, text="Project Structure", padding=10)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Create canvas and scrollbar for the tree
        self.canvas = tk.Canvas(tree_frame)
        scrollbar = ttk.Scrollbar(
            tree_frame, orient="vertical", command=self.canvas.yview
        )
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Bottom frame for controls
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill="x", padx=10, pady=5)

        # Process button
        ttk.Button(bottom_frame, text="Extract Code", command=self.process_files).pack(
            side="left", pady=5
        )

        # Progress bar
        self.progress = ttk.Progressbar(bottom_frame, length=400, mode="determinate")
        self.progress.pack(side="left", padx=10, pady=5)

        # Status label
        self.status_label = ttk.Label(bottom_frame, text="")
        self.status_label.pack(side="left", pady=5)

    def browse_source(self):
        folder = filedialog.askdirectory()
        if folder:
            self.source_path.set(folder)
            self.refresh_tree()
            self.save_config()

    def browse_output(self):
        file = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if file:
            self.output_path.set(file)
            self.save_config()

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def create_tree_item(self, parent_path, parent_widget, level=0):
        try:
            path = Path(parent_path)

            # Create frame for this level
            frame = ttk.Frame(parent_widget)
            frame.pack(fill="x", padx=level * 20)

            # Create TreeItem
            tree_item = TreeItem(path)
            self.tree_items[str(path)] = tree_item

            # Checkbox
            chk = ttk.Checkbutton(frame, variable=tree_item.checked)
            chk.pack(side="left")

            if path.is_dir():
                # Expand button if directory has contents
                has_contents = any(True for _ in path.iterdir())
                if has_contents:
                    btn = ttk.Button(
                        frame,
                        text="+",
                        width=2,
                        command=lambda p=path, f=frame: self.toggle_expand(p, f),
                    )
                    btn.pack(side="left")
                else:
                    ttk.Label(frame, width=2).pack(side="left")
            else:
                ttk.Label(frame, width=2).pack(side="left")

            # Item name with icon
            icon = "📄 " if path.is_file() else "📁 "
            ttk.Label(frame, text=icon + (path.name or str(path))).pack(side="left")

        except PermissionError:
            print(f"Permission denied: {parent_path}")
        except Exception as e:
            print(f"Error processing {parent_path}: {e}")

    def toggle_expand(self, path, parent_frame):
        tree_item = self.tree_items[str(path)]

        if not tree_item.expanded:
            # Change button text
            parent_frame.winfo_children()[1].configure(text="-")

            # Create a container frame for the children
            container_frame = ttk.Frame(parent_frame.master)
            container_frame.pack(fill="x", after=parent_frame)
            tree_item.container = container_frame  # Store reference to container

            # Add contents
            try:
                items = sorted(
                    Path(path).iterdir(), key=lambda p: (p.is_file(), p.name)
                )
                for item in items:
                    self.create_tree_item(item, container_frame, level=len(path.parts))
            except PermissionError:
                messagebox.showwarning(
                    "Permission Denied", f"Cannot access contents of {path.name}"
                )

            tree_item.expanded = True
            tree_item.is_loaded = True
        else:
            # Change button text
            parent_frame.winfo_children()[1].configure(text="+")

            # Remove contents by destroying the container frame
            if hasattr(tree_item, "container") and tree_item.container:
                tree_item.container.destroy()
                tree_item.container = None

            tree_item.expanded = False

    def refresh_tree(self):
        # Clear existing tree
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.tree_items.clear()

        # Create new tree
        if self.source_path.get():
            self.create_tree_item(self.source_path.get(), self.scrollable_frame)

    def should_process_path(self, path):
        path_str = str(path)
        for item_path, tree_item in self.tree_items.items():
            if path_str.startswith(item_path) and tree_item.checked.get():
                return self.include_mode.get()
        return not self.include_mode.get()

    def process_files(self):
        source = self.source_path.get()
        output = self.output_path.get()

        if not source or not output:
            messagebox.showerror(
                "Error", "Please select both source directory and output file"
            )
            return

        try:
            self.progress["value"] = 0
            self.status_label["text"] = "Processing..."
            self.root.update()

            total_files = sum(
                1
                for p in Path(source).rglob("*")
                if p.is_file() and self.should_process_path(p)
            )
            processed_files = 0

            with open(output, "w", encoding="utf-8") as f:
                # Minimal header
                mode_str = "+" if self.include_mode.get() else "-"
                f.write(f"# Project Extract ({mode_str}checked)\n")

                # Write structure with minimal characters
                f.write("\n# Structure\n")

                def write_structure(path, level=0):
                    if self.should_process_path(path):
                        indent = " " * level * 2  # Use 2 spaces for indentation
                        prefix = ">" if path.is_dir() else "-"
                        f.write(f"{indent}{prefix} {path.name}\n")
                        if path.is_dir():
                            for child in sorted(
                                path.iterdir(), key=lambda p: (p.is_file(), p.name)
                            ):
                                write_structure(child, level + 1)

                write_structure(Path(source))

                # Write file contents with minimal separators
                f.write("\n# Contents\n")

                for path in Path(source).rglob("*"):
                    if path.is_file() and self.should_process_path(path):
                        try:
                            rel_path = path.relative_to(source)
                            f.write(f"\n@ {rel_path}\n")  # Use @ as file indicator

                            try:
                                content = path.read_text(encoding="utf-8")
                                # Remove trailing whitespace and extra blank lines
                                cleaned_content = "\n".join(
                                    line.rstrip() for line in content.splitlines()
                                ).strip()
                                f.write(cleaned_content + "\n")
                            except UnicodeDecodeError:
                                f.write("[binary]\n")

                            processed_files += 1
                            self.progress["value"] = (
                                processed_files / total_files
                            ) * 100
                            self.root.update()

                        except Exception as e:
                            f.write(f"[error: {e}]\n")

            self.status_label["text"] = "Complete!"
            self.save_config()  # Save configuration after successful processing
            messagebox.showinfo("Success", "Extraction complete!")

        except Exception as e:
            self.status_label["text"] = "Error occurred."
            messagebox.showerror("Error", f"Error: {str(e)}")

    def on_closing(self):
        """Handle window closing event"""
        self.save_config()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = CodeExtractorGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)  # Handle window closing
    root.mainloop()
