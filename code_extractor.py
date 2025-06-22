import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import os
import json
import hashlib
import datetime


class TreeItem:
    def __init__(self, path, parent=None):
        self.path = Path(path)
        self.parent = parent
        self.children = []
        self.expanded = False
        self.checked = tk.BooleanVar(value=False)
        self.is_loaded = False
        self.is_file = self.path.is_file()
        self.container = None
        self.expand_button = None


class ModernCodeExtractorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Code Extractor Pro")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)

        # Modern Windows styling
        self.setup_modern_style()

        self.tree_items = {}
        self.include_mode = tk.BooleanVar(value=True)
        self.filenames_only = tk.BooleanVar(value=False)  # New option

        # Load configuration
        self.config_file = Path.home() / ".code_extractor_config.json"
        self.load_config()

        self.create_modern_gui()

        # Load saved paths and selections
        if self.config.get("last_source"):
            self.source_path.set(self.config["last_source"])
            self.refresh_tree()
        if self.config.get("last_output"):
            self.output_path.set(self.config["last_output"])

    def setup_modern_style(self):
        """Configure modern Windows-style theming"""
        style = ttk.Style()

        # Try to use modern Windows theme
        try:
            style.theme_use("vista")  # Modern Windows theme
        except:
            try:
                style.theme_use("winnative")
            except:
                pass

        # Configure modern colors and styles
        style.configure("Modern.TFrame", background="#f0f0f0")

        # --- START OF CORRECTION ---
        # Configure the default TLabelFrame style directly
        style.configure(
            "TLabelFrame", background="#ffffff", relief="flat", borderwidth=1
        )
        # Configure the label within the default TLabelFrame
        style.configure(
            "TLabelFrame.Label",
            background="#ffffff",
            foreground="#333333",
            font=("Segoe UI", 10, "bold"),
        )
        # --- END OF CORRECTION ---

        style.configure("Modern.TButton", padding=(12, 8))
        style.configure("Accent.TButton", background="#0078d4", foreground="white")
        style.configure("Success.TButton", background="#107c10", foreground="white")

        # Configure the root window
        self.root.configure(bg="#f0f0f0")

    def load_config(self):
        try:
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    self.config = json.load(f)
                    # Ensure the 'selections' key exists to handle old config files.
                    if "selections" not in self.config:
                        self.config["selections"] = {}
                    # Keep only the last 10 entries
                    for key in ["recent_sources", "recent_outputs"]:
                        if key in self.config:
                            self.config[key] = self.config[key][-10:]
            else:
                self.config = {
                    "last_source": "",
                    "last_output": "",
                    "recent_sources": [],
                    "recent_outputs": [],
                    "selections": {},  # Store selections per directory
                }
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config = {
                "last_source": "",
                "last_output": "",
                "recent_sources": [],
                "recent_outputs": [],
                "selections": {},
            }

    def save_config(self):
        try:
            # Update last used paths
            self.config["last_source"] = self.source_path.get()
            self.config["last_output"] = self.output_path.get()

            # Save current selections
            if self.source_path.get():
                self.save_selections()

            # Update recent lists without duplicates
            for path_var, config_key in [
                (self.source_path, "recent_sources"),
                (self.output_path, "recent_outputs"),
            ]:
                if path_var.get():
                    if config_key not in self.config:
                        self.config[config_key] = []
                    if path_var.get() in self.config[config_key]:
                        self.config[config_key].remove(path_var.get())
                    self.config[config_key].append(path_var.get())
                    self.config[config_key] = self.config[config_key][
                        -10:
                    ]  # Keep last 10

            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def save_selections(self):
        """Save current checkbox selections for the current directory"""
        if not self.source_path.get():
            return

        source_hash = hashlib.md5(self.source_path.get().encode()).hexdigest()
        selections = {}

        for path_str, tree_item in self.tree_items.items():
            if tree_item.checked.get():
                # Store relative path from source
                try:
                    rel_path = str(Path(path_str).relative_to(self.source_path.get()))
                    selections[rel_path] = True
                except ValueError:
                    pass  # Path is not relative to source

        self.config["selections"][source_hash] = selections

    def load_selections(self):
        """Load previously saved selections for the current directory"""
        if not self.source_path.get():
            return

        source_hash = hashlib.md5(self.source_path.get().encode()).hexdigest()
        selections = self.config.get("selections", {}).get(source_hash, {})

        for rel_path, checked in selections.items():
            try:
                full_path = str(Path(self.source_path.get()) / rel_path)
                if full_path in self.tree_items:
                    self.tree_items[full_path].checked.set(checked)
            except Exception:
                pass  # Path may no longer exist

    def create_modern_gui(self):
        # Main container with padding
        main_container = ttk.Frame(self.root, style="Modern.TFrame")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Header section
        # --- START OF CORRECTION ---
        # Removed style="Header.TLabelFrame"
        header_frame = ttk.LabelFrame(
            main_container,
            text="📁 Project Settings",
            padding=20,
        )
        # --- END OF CORRECTION ---
        header_frame.pack(fill="x", pady=(0, 15))

        self.create_path_selection(header_frame)
        self.create_options_section(header_frame)

        tree_frame = ttk.LabelFrame(
            main_container,
            text="📂 Project Structure",
            padding=15,
        )
        tree_frame.pack(fill="both", expand=True, pady=(0, 15))

        self.create_tree_view(tree_frame)

        # Control buttons section
        self.create_control_buttons(main_container)

    def create_path_selection(self, parent):
        # Source directory section with modern layout
        source_section = ttk.Frame(parent)
        source_section.pack(fill="x", pady=(0, 15))

        ttk.Label(
            source_section, text="Source Directory:", font=("Segoe UI", 9, "bold")
        ).pack(anchor="w")

        source_input_frame = ttk.Frame(source_section)
        source_input_frame.pack(fill="x", pady=(5, 0))

        self.source_path = tk.StringVar()
        source_entry = ttk.Entry(
            source_input_frame,
            textvariable=self.source_path,
            font=("Segoe UI", 9),
            width=80,
        )
        source_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ttk.Button(
            source_input_frame,
            text="📁 Browse",
            command=self.browse_source,
            style="Modern.TButton",
        ).pack(side="right")

        # Add recent sources dropdown
        self.create_recent_dropdown(
            source_input_frame,
            source_entry,
            "recent_sources",
            lambda p: (self.source_path.set(p), self.refresh_tree()),
        )

        # Output file section
        output_section = ttk.Frame(parent)
        output_section.pack(fill="x", pady=(10, 0))

        ttk.Label(
            output_section, text="Output File:", font=("Segoe UI", 9, "bold")
        ).pack(anchor="w")

        output_input_frame = ttk.Frame(output_section)
        output_input_frame.pack(fill="x", pady=(5, 0))

        self.output_path = tk.StringVar()
        output_entry = ttk.Entry(
            output_input_frame,
            textvariable=self.output_path,
            font=("Segoe UI", 9),
            width=80,
        )
        output_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ttk.Button(
            output_input_frame,
            text="💾 Save As",
            command=self.browse_output,
            style="Modern.TButton",
        ).pack(side="right")

        # Add recent outputs dropdown
        self.create_recent_dropdown(
            output_input_frame,
            output_entry,
            "recent_outputs",
            lambda p: self.output_path.set(p),
        )

    def create_recent_dropdown(self, parent, entry_widget, config_key, command):
        """Create a dropdown arrow for recent items"""
        if self.config.get(config_key):
            dropdown_btn = ttk.Button(
                parent,
                text="▼",
                width=3,
                command=lambda: self.show_recent_menu(
                    dropdown_btn, config_key, command
                ),
            )
            dropdown_btn.pack(side="right", padx=(5, 0))

    def show_recent_menu(self, button, config_key, command):
        """Show recent items menu"""
        menu = tk.Menu(self.root, tearoff=0)
        for path in reversed(self.config.get(config_key, [])):
            menu.add_command(label=path, command=lambda p=path: command(p))

        # Position menu below button
        x = button.winfo_rootx()
        y = button.winfo_rooty() + button.winfo_height()
        menu.post(x, y)

    def create_options_section(self, parent):
        options_frame = ttk.LabelFrame(parent, text="⚙️ Options", padding=10)
        options_frame.pack(fill="x", pady=(15, 0))

        # Mode selection with modern radio buttons
        mode_frame = ttk.Frame(options_frame)
        mode_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(
            mode_frame, text="Selection Mode:", font=("Segoe UI", 9, "bold")
        ).pack(anchor="w")

        radio_frame = ttk.Frame(mode_frame)
        radio_frame.pack(fill="x", pady=(5, 0))

        ttk.Radiobutton(
            radio_frame,
            text="✅ Include checked items",
            variable=self.include_mode,
            value=True,
        ).pack(side="left", padx=(0, 20))
        ttk.Radiobutton(
            radio_frame,
            text="❌ Exclude checked items",
            variable=self.include_mode,
            value=False,
        ).pack(side="left")

        # Output options
        output_options_frame = ttk.Frame(options_frame)
        output_options_frame.pack(fill="x")

        ttk.Label(
            output_options_frame, text="Output Content:", font=("Segoe UI", 9, "bold")
        ).pack(anchor="w")

        content_frame = ttk.Frame(output_options_frame)
        content_frame.pack(fill="x", pady=(5, 0))

        ttk.Checkbutton(
            content_frame,
            text="📝 Filenames only (no file content)",
            variable=self.filenames_only,
        ).pack(anchor="w")

    def create_tree_view(self, parent):
        # Create modern tree container with better scrolling
        tree_container = ttk.Frame(parent)
        tree_container.pack(fill="both", expand=True)

        # Canvas with modern scrollbar
        self.canvas = tk.Canvas(tree_container, bg="white", highlightthickness=0)

        # Modern scrollbar
        scrollbar = ttk.Scrollbar(
            tree_container, orient="vertical", command=self.canvas.yview
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

        # Enhanced mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Shift-MouseWheel>", self._on_horizontal_mousewheel)

        # Add tree controls
        tree_controls = ttk.Frame(parent)
        tree_controls.pack(fill="x", pady=(10, 0))

        ttk.Button(tree_controls, text="✅ Select All", command=self.select_all).pack(
            side="left", padx=(0, 10)
        )
        ttk.Button(
            tree_controls, text="❌ Deselect All", command=self.deselect_all
        ).pack(side="left", padx=(0, 10))
        ttk.Button(tree_controls, text="🔄 Refresh", command=self.refresh_tree).pack(
            side="left"
        )

    def create_control_buttons(self, parent):
        # Bottom control section with modern buttons
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill="x")

        # Left side - Extract button
        left_controls = ttk.Frame(control_frame)
        left_controls.pack(side="left")

        extract_btn = ttk.Button(
            left_controls,
            text="🚀 Extract Code",
            command=self.process_files,
            style="Success.TButton",
        )
        extract_btn.pack(side="left", padx=(0, 20))

        # Center - Progress and status
        center_controls = ttk.Frame(control_frame)
        center_controls.pack(side="left", fill="x", expand=True)

        self.progress = ttk.Progressbar(center_controls, length=300, mode="determinate")
        self.progress.pack(side="left", padx=(0, 15))

        self.status_label = ttk.Label(
            center_controls, text="Ready", font=("Segoe UI", 9)
        )
        self.status_label.pack(side="left")

    def browse_source(self):
        folder = filedialog.askdirectory(title="Select Source Directory")
        if folder:
            self.source_path.set(folder)
            self.refresh_tree()
            self.save_config()

    def browse_output(self):
        file = filedialog.asksaveasfilename(
            title="Save Extracted Code As",
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("Markdown files", "*.md"),
                ("All files", "*.*"),
            ],
        )
        if file:
            self.output_path.set(file)
            self.save_config()

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_horizontal_mousewheel(self, event):
        self.canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

    def create_tree_item(self, parent_path, parent_widget, level=0):
        try:
            path = Path(parent_path)

            # Create modern item frame
            item_frame = ttk.Frame(parent_widget)
            item_frame.pack(fill="x", pady=1)

            # Indentation frame
            indent_frame = ttk.Frame(item_frame)
            indent_frame.pack(side="left", padx=(level * 25, 0))

            # Create TreeItem
            tree_item = TreeItem(path)
            self.tree_items[str(path)] = tree_item

            # Modern checkbox
            chk_frame = ttk.Frame(indent_frame)
            chk_frame.pack(side="left")

            chk = ttk.Checkbutton(chk_frame, variable=tree_item.checked)
            chk.pack(side="left")

            # Expand/collapse button for directories
            if path.is_dir():
                try:
                    has_contents = any(True for _ in path.iterdir())
                    if has_contents:
                        btn = ttk.Button(
                            chk_frame,
                            text="▶",
                            width=3,
                            command=lambda p=path, f=item_frame: self.toggle_expand(
                                p, f
                            ),
                        )
                        btn.pack(side="left", padx=(5, 0))
                        tree_item.expand_button = btn  # <-- ADD THIS LINE
                    else:
                        ttk.Label(chk_frame, width=3).pack(side="left", padx=(5, 0))
                except PermissionError:
                    ttk.Label(chk_frame, text="🔒", width=3).pack(
                        side="left", padx=(5, 0)
                    )
            else:
                ttk.Label(chk_frame, width=3).pack(side="left", padx=(5, 0))

            # Item label with modern icons and styling
            label_frame = ttk.Frame(indent_frame)
            label_frame.pack(side="left", fill="x", expand=True, padx=(10, 0))

            if path.is_file():
                icon = self.get_file_icon(path)
            else:
                icon = "📁"

            item_label = ttk.Label(
                label_frame,
                text=f"{icon} {path.name or str(path)}",
                font=("Segoe UI", 9),
            )
            item_label.pack(side="left")

            # Add file size for files
            if path.is_file():
                try:
                    size = path.stat().st_size
                    size_str = self.format_file_size(size)
                    size_label = ttk.Label(
                        label_frame,
                        text=f"({size_str})",
                        font=("Segoe UI", 8),
                        foreground="gray",
                    )
                    size_label.pack(side="left", padx=(10, 0))
                except:
                    pass

        except PermissionError:
            print(f"Permission denied: {parent_path}")
        except Exception as e:
            print(f"Error processing {parent_path}: {e}")

    def get_file_icon(self, path):
        """Get appropriate icon for file type"""
        suffix = path.suffix.lower()
        icon_map = {
            ".py": "🐍",
            ".js": "📜",
            ".html": "🌐",
            ".css": "🎨",
            ".json": "📋",
            ".txt": "📄",
            ".md": "📝",
            ".yml": "⚙️",
            ".yaml": "⚙️",
            ".xml": "📰",
            ".png": "🖼️",
            ".jpg": "🖼️",
            ".jpeg": "🖼️",
            ".gif": "🖼️",
            ".svg": "🖼️",
            ".zip": "📦",
            ".tar": "📦",
            ".gz": "📦",
            ".rar": "📦",
            ".exe": "⚙️",
            ".bat": "⚙️",
            ".sh": "⚙️",
        }
        return icon_map.get(suffix, "📄")

    def format_file_size(self, size):
        """Format file size in human readable format"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def toggle_expand(self, path, parent_frame):
        tree_item = self.tree_items[str(path)]
        button = tree_item.expand_button
        if button is None:
            return

        if not tree_item.expanded:
            button.configure(text="▼")

            # Create container for children
            container_frame = ttk.Frame(parent_frame.master)
            container_frame.pack(fill="x", after=parent_frame)
            tree_item.container = container_frame

            # Add contents
            try:
                items = sorted(
                    Path(path).iterdir(), key=lambda p: (p.is_file(), p.name.lower())
                )
                for item in items:
                    self.create_tree_item(
                        item,
                        container_frame,
                        level=len(Path(path).parts)
                        - len(Path(self.source_path.get()).parts),
                    )
            except PermissionError:
                messagebox.showwarning(
                    "Permission Denied", f"Cannot access contents of {path.name}"
                )

            tree_item.expanded = True
            tree_item.is_loaded = True

            # Load saved selections after expanding
            self.load_selections()
        else:
            button.configure(text="▶")

            if hasattr(tree_item, "container") and tree_item.container:
                tree_item.container.destroy()
                tree_item.container = None

            tree_item.expanded = False

    def select_all(self):
        """Select all visible items"""
        for tree_item in self.tree_items.values():
            tree_item.checked.set(True)

    def deselect_all(self):
        """Deselect all items"""
        for tree_item in self.tree_items.values():
            tree_item.checked.set(False)

    def refresh_tree(self):
        # Save current selections before refreshing
        if self.source_path.get():
            self.save_selections()

        # Clear existing tree
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.tree_items.clear()

        # Create new tree
        if self.source_path.get():
            self.create_tree_item(self.source_path.get(), self.scrollable_frame)
            # Load saved selections after creating tree
            self.root.after(100, self.load_selections)  # Delay to ensure tree is built

    def should_process_path(self, path):
        path_str = str(path)

        # Check if this specific path is checked
        if path_str in self.tree_items:
            if self.tree_items[path_str].checked.get():
                return self.include_mode.get()

        # Check if any parent directory affects this path
        for item_path, tree_item in self.tree_items.items():
            if (
                path_str.startswith(item_path)
                and item_path != path_str
                and tree_item.checked.get()
            ):
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

            # Count files to process
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
                self.status_label["text"] = "Ready"
                return

            with open(output, "w", encoding="utf-8") as f:
                # Modern header
                mode_str = "Include" if self.include_mode.get() else "Exclude"
                content_type = (
                    "Filenames Only" if self.filenames_only.get() else "Full Content"
                )
                f.write(f"# 🚀 Code Extraction Report\n")
                f.write(f"**Source:** {source}\n")
                f.write(f"**Mode:** {mode_str} checked items\n")
                f.write(f"**Content:** {content_type}\n")
                f.write(f"**Files Processed:** {total_files}\n")
                f.write(
                    f"**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                )

                # Write structure
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
                            icon = self.get_file_icon(path)
                            size = ""
                            try:
                                file_size = path.stat().st_size
                                size = f" ({self.format_file_size(file_size)})"
                            except:
                                pass
                            f.write(f"{indent}{icon} {path.name}{size}\n")

                write_structure(Path(source))
                f.write("```\n\n")

                # Write file contents (if not filenames only)
                if not self.filenames_only.get():
                    f.write("## 📄 File Contents\n\n")

                    for i, path in enumerate(files_to_process):
                        try:
                            rel_path = path.relative_to(source)
                            icon = self.get_file_icon(path)
                            f.write(f"### {icon} `{rel_path}`\n\n")

                            try:
                                content = path.read_text(encoding="utf-8")
                                # Determine language for syntax highlighting
                                lang = self.get_language_for_highlighting(path.suffix)
                                f.write(f"```{lang}\n")
                                f.write(content.rstrip() + "\n")
                                f.write("```\n\n")
                            except UnicodeDecodeError:
                                f.write(
                                    "```\n[Binary file - content not displayed]\n```\n\n"
                                )

                            # Update progress
                            progress = ((i + 1) / total_files) * 100
                            self.progress["value"] = progress
                            self.status_label["text"] = (
                                f"Processing {i + 1}/{total_files}..."
                            )
                            self.root.update()

                        except Exception as e:
                            f.write(f"```\n[Error reading file: {e}]\n```\n\n")

            self.progress["value"] = 100
            self.status_label["text"] = f"✅ Complete! Processed {total_files} files"
            self.save_config()
            messagebox.showinfo(
                "Success",
                f"Extraction complete!\n\nProcessed {total_files} files\nSaved to: {output}",
            )

        except Exception as e:
            self.status_label["text"] = "❌ Error occurred"
            messagebox.showerror("Error", f"Error during extraction:\n{str(e)}")

    def get_language_for_highlighting(self, suffix):
        """Get language identifier for syntax highlighting"""
        lang_map = {
            ".py": "python",
            ".js": "javascript",
            ".html": "html",
            ".css": "css",
            ".json": "json",
            ".xml": "xml",
            ".yml": "yaml",
            ".yaml": "yaml",
            ".sh": "bash",
            ".bat": "batch",
            ".ps1": "powershell",
            ".c": "c",
            ".cpp": "cpp",
            ".java": "java",
            ".cs": "csharp",
            ".php": "php",
            ".rb": "ruby",
            ".go": "go",
            ".rs": "rust",
            ".sql": "sql",
            ".md": "markdown",
        }
        return lang_map.get(suffix.lower(), "text")

    def on_closing(self):
        """Handle window closing event"""
        self.save_config()
        self.root.destroy()


# Import datetime for timestamp
import datetime

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernCodeExtractorGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
