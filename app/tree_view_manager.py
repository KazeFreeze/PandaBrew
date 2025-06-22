import tkinter as tk
import ttkbootstrap as ttkb
from ttkbootstrap.dialogs import Messagebox
from pathlib import Path
from utils.helpers import get_icon, format_file_size


class TreeItem:
    """
    Represents an item in the tree view, which can be a file or a directory.
    """

    def __init__(self, path):
        self.path = Path(path)
        self.expanded = False
        self.checked = tk.BooleanVar(value=False)
        self.container = None
        self.expand_button = None


class TreeViewManager:
    """
    Manages the creation, display, and interaction of the file and directory
    tree view for a single tab.
    """

    def __init__(self, app_instance, tab_id):
        self.app = app_instance
        self.tab_id = tab_id
        self.tree_items = {}

    def get_tab_data(self):
        return self.app.tabs.get(self.tab_id)

    def create_tree_item_widget(self, path, parent_widget, level=0):
        """
        Creates the UI widget for a single item (file or directory) in the tree view.
        """
        try:
            item_frame = ttkb.Frame(parent_widget)
            item_frame.pack(fill="x", pady=0)

            indent_frame = ttkb.Frame(item_frame)
            indent_frame.pack(side="left", padx=(level * 20, 0))

            if str(path) not in self.tree_items:
                self.tree_items[str(path)] = TreeItem(path)
            tree_item = self.tree_items[str(path)]

            # MODIFIED: Use new expander icons and smaller button
            if path.is_dir():
                try:
                    has_contents = any(path.iterdir())
                    if has_contents:
                        btn = ttkb.Button(
                            indent_frame,
                            text="▶",
                            width=2,
                            command=lambda p=path, f=item_frame: self.toggle_expand(
                                p, f
                            ),
                            bootstyle="link",  # Use link style for minimal appearance
                        )
                        btn.pack(side="left")
                        tree_item.expand_button = btn
                    else:
                        ttkb.Label(indent_frame, text="  ").pack(
                            side="left"
                        )  # Placeholder for alignment
                except PermissionError:
                    ttkb.Label(indent_frame, text="! ").pack(side="left")

            chk = ttkb.Checkbutton(indent_frame, variable=tree_item.checked)
            chk.pack(side="left")

            label_frame = ttkb.Frame(item_frame)
            label_frame.pack(side="left", fill="x", expand=True, padx=5)

            icon = get_icon(path)
            item_label = ttkb.Label(
                label_frame,
                text=f" {icon} {path.name}",
                compound="left",
                font=("Segoe UI", 9),
            )
            item_label.pack(side="left")

            if path.is_file():
                try:
                    size_str = format_file_size(path.stat().st_size)
                    size_label = ttkb.Label(
                        label_frame,
                        text=f"({size_str})",
                        font=("Segoe UI", 8, "italic"),
                        bootstyle="secondary",
                    )
                    size_label.pack(side="left", padx=10)
                except (IOError, PermissionError):
                    pass

        except (IOError, PermissionError) as e:
            print(f"Skipping due to error: {e}")

    def toggle_expand(self, path, parent_frame):
        """
        Expands or collapses a directory, loading its contents on first expansion.
        """
        tree_item = self.tree_items.get(str(path))
        if not tree_item or not tree_item.expand_button:
            return

        button = tree_item.expand_button

        if not tree_item.expanded:
            button.configure(text="▼")  # MODIFIED: Expanded icon
            if not tree_item.container:
                container_frame = ttkb.Frame(parent_frame.master)
                container_frame.pack(fill="x", after=parent_frame)
                tree_item.container = container_frame
                try:
                    tab_data = self.get_tab_data()
                    source_root_path = Path(tab_data["source_path"].get())
                    current_level = len(path.parts) - len(source_root_path.parts)

                    items = sorted(
                        path.iterdir(), key=lambda p: (p.is_file(), p.name.lower())
                    )
                    for item_path in items:
                        self.create_tree_item_widget(
                            item_path, container_frame, level=current_level + 1
                        )

                    self.app.config_manager.load_selections(tab_data)
                except Exception as e:
                    print(f"Error expanding {path}: {e}")
            tree_item.expanded = True
        else:
            button.configure(text="▶")  # MODIFIED: Collapsed icon
            if tree_item.container:
                for widget in tree_item.container.winfo_children():
                    widget.destroy()
                tree_item.container.destroy()
                tree_item.container = None
            tree_item.expanded = False

    def select_all(self):
        for tree_item in self.tree_items.values():
            tree_item.checked.set(True)

    def deselect_all(self):
        for tree_item in self.tree_items.values():
            tree_item.checked.set(False)

    def refresh_tree(self):
        """
        Refreshes the tree view for its tab, clearing the old view and building a new one.
        """
        tab_data = self.get_tab_data()
        if not tab_data:
            return

        if tab_data["source_path"].get():
            self.app.config_manager.save_selections(tab_data)

        for widget in tab_data["scrollable_frame"].winfo_children():
            widget.destroy()
        self.tree_items.clear()

        source_path_str = tab_data["source_path"].get()
        if source_path_str:
            source_path = Path(source_path_str)
            if source_path.exists() and source_path.is_dir():
                self.create_tree_item_widget(
                    source_path, tab_data["scrollable_frame"], level=0
                )
                self.app.root.after(
                    50, lambda: self.app.config_manager.load_selections(tab_data)
                )
            else:
                ttkb.Label(
                    tab_data["scrollable_frame"],
                    text=f"Path not found: {source_path_str}",
                    bootstyle="danger",
                ).pack()
