import tkinter as tk
import ttkbootstrap as ttkb
from pathlib import Path
from utils.helpers import format_file_size


class TreeItem:
    """
    Represents a visual item in the tree view, which can be a file or a directory.
    """

    def __init__(self, path):
        self.path = Path(path)
        self.expanded = False
        self.checked = tk.BooleanVar()
        self.widget = None  # The main frame for this item
        self.container = None  # Frame for children widgets
        self.expander_label = None  # Label for [+] / [-]
        # The base prefix for any children of this item (e.g., "│   ")
        self.child_base_prefix = ""


class TreeViewManager:
    """
    Manages the creation, display, and interaction of the file and directory
    tree view for a single tab. It now handles persistent selections and
    parent/child checkbox logic with a classic ASCII tree structure.
    """

    def __init__(self, app_instance, tab_id):
        self.app = app_instance
        self.tab_id = tab_id
        # A dictionary to hold the GUI widgets for visible items
        self.tree_items = {}
        # The canonical set of all checked paths (persisted)
        self.checked_paths = set()

    def get_tab_data(self):
        """Safely retrieves the data for the current tab."""
        return self.app.tabs.get(self.tab_id)

    def _build_tree_level(self, parent_widget, paths, base_prefix=""):
        """
        Builds one level of the tree view.
        """
        paths = sorted(list(paths), key=lambda p: (p.is_file(), p.name.lower()))
        for i, path in enumerate(paths):
            is_last = i == (len(paths) - 1)
            connector = "└── " if is_last else "├── "
            child_base_prefix = base_prefix + ("    " if is_last else "│   ")
            self.create_tree_item_widget(
                path, parent_widget, base_prefix + connector, child_base_prefix
            )

    def create_tree_item_widget(self, path, parent_widget, prefix, child_base_prefix):
        """
        Creates the UI widget for a single item (file or directory) in the tree.
        """
        path_str = str(path)
        if path_str in self.tree_items:
            return  # Avoid duplicating widgets

        item_frame = ttkb.Frame(parent_widget)
        item_frame.pack(fill="x", pady=0, padx=0)

        # --- ASCII Prefix and Expander ---
        prefix_label = ttkb.Label(item_frame, text=prefix, font=("Courier", 10))
        prefix_label.pack(side="left")

        tree_item = TreeItem(path)
        tree_item.widget = item_frame
        tree_item.child_base_prefix = child_base_prefix

        is_expandable = False
        if path.is_dir():
            try:
                if any(path.iterdir()):
                    is_expandable = True
            except PermissionError:
                pass

        if is_expandable:
            expander = ttkb.Label(
                item_frame, text="+", font=("Courier", 10, "bold"), width=2
            )
            expander.bind("<Button-1>", lambda e, p=path: self.toggle_expand(p))
        else:
            expander = ttkb.Label(
                item_frame, text=" ", width=2
            )  # Placeholder for alignment

        expander.pack(side="left")
        tree_item.expander_label = expander

        # --- Checkbox ---
        tree_item.checked.set(path_str in self.checked_paths)
        chk = ttkb.Checkbutton(
            item_frame,
            variable=tree_item.checked,
            command=lambda p=path_str, v=tree_item.checked: self.on_item_check(p, v),
        )
        chk.pack(side="left")
        self.tree_items[path_str] = tree_item

        # --- Name and Size ---
        label_frame = ttkb.Frame(item_frame)
        label_frame.pack(side="left", fill="x", expand=True, padx=4)

        name_label = ttkb.Label(
            label_frame,
            text=f" {path.name}",
            compound="left",
            font=("Segoe UI", 9),
        )
        name_label.pack(side="left")

        if path.is_file():
            try:
                size_str = format_file_size(path.stat().st_size)
                ttkb.Label(
                    label_frame,
                    text=f"({size_str})",
                    font=("Segoe UI", 8, "italic"),
                    bootstyle="secondary",
                ).pack(side="left", padx=10)
            except (IOError, PermissionError):
                pass
        elif is_expandable:
            # Also bind name label for easier expanding/collapsing
            name_label.bind("<Button-1>", lambda e, p=path: self.toggle_expand(p))

    def toggle_expand(self, path):
        """
        Expands or collapses a directory, loading its contents on first expansion.
        """
        path_str = str(path)
        tree_item = self.tree_items.get(path_str)
        if not tree_item or not tree_item.expander_label:
            return

        if not tree_item.expanded:
            tree_item.expander_label.config(text="-")
            if not tree_item.container:
                # Create a container for child items
                tree_item.container = ttkb.Frame(tree_item.widget.master)
                tree_item.container.pack(fill="x", after=tree_item.widget)
                try:
                    children = path.iterdir()
                    self._build_tree_level(
                        tree_item.container, children, tree_item.child_base_prefix
                    )
                except Exception as e:
                    print(f"Error expanding {path}: {e}")
            tree_item.expanded = True
        else:
            tree_item.expander_label.config(text="+")
            if tree_item.container:
                # To collapse, destroy the container frame and all its children
                tree_item.container.destroy()
                tree_item.container = None
            tree_item.expanded = False
            # Remove collapsed items from our visible items dict
            self.tree_items = {
                p: i
                for p, i in self.tree_items.items()
                if not Path(p).is_relative_to(path) or p == path_str
            }

    def on_item_check(self, path_str, var):
        """
        Handles the logic when a checkbox is clicked. It updates the canonical
        checked_paths set and propagates the change to all descendant items.
        """
        is_checked = var.get()
        path = Path(path_str)

        paths_to_update = {path_str}
        if path.is_dir():
            try:
                for child in path.rglob("*"):
                    paths_to_update.add(str(child))
            except PermissionError:
                pass

        if is_checked:
            self.checked_paths.update(paths_to_update)
        else:
            self.checked_paths.difference_update(paths_to_update)

        for p_str in paths_to_update:
            if p_str in self.tree_items:
                self.tree_items[p_str].checked.set(is_checked)

    def select_all(self):
        """Selects all files and folders for the current source."""
        tab_data = self.get_tab_data()
        source_path_str = tab_data["source_path"].get()
        if not source_path_str:
            return

        source_path = Path(source_path_str)
        self.checked_paths.add(str(source_path))
        for path in source_path.rglob("*"):
            self.checked_paths.add(str(path))

        for item in self.tree_items.values():
            item.checked.set(True)

    def deselect_all(self):
        """Deselects all files and folders."""
        self.checked_paths.clear()
        for item in self.tree_items.values():
            item.checked.set(False)

    def refresh_tree(self):
        """
        Refreshes the tree view, clearing the old view and building a new one
        based on the filesystem and the persistent checked_paths set.
        """
        tab_data = self.get_tab_data()
        if not tab_data:
            return

        for widget in tab_data["scrollable_frame"].winfo_children():
            widget.destroy()
        self.tree_items.clear()

        source_path_str = tab_data["source_path"].get()
        if source_path_str:
            source_path = Path(source_path_str)
            if source_path.exists() and source_path.is_dir():
                self.app.config_manager.load_selections(tab_data)

                # Start building the tree from the root
                self.create_tree_item_widget(
                    source_path, tab_data["scrollable_frame"], "", ""
                )
            else:
                ttkb.Label(
                    tab_data["scrollable_frame"],
                    text=f"Path not found or is not a directory: {source_path_str}",
                    bootstyle="danger",
                ).pack()
