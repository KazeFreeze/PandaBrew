import tkinter as tk
import ttkbootstrap as ttkb
from ttkbootstrap.dialogs import Messagebox
from pathlib import Path
from utils.helpers import get_icon, format_file_size


class TreeItem:
    """
    Represents an item in the tree view, which can be a file or a directory.
    """

    def __init__(self, path, parent=None):
        """
        Initializes a TreeItem.
        """
        self.path = Path(path)
        self.parent = parent
        self.children = []
        self.expanded = False
        self.checked = tk.BooleanVar(value=False)
        self.is_loaded = False
        self.is_file = self.path.is_file()
        self.container = None
        self.expand_button = None


class TreeViewManager:
    """
    Manages the creation, display, and interaction of the file and directory tree view.
    """

    def __init__(self, app_instance):
        """
        Initializes the TreeViewManager.
        """
        self.app = app_instance
        self.tree_items = {}

    def create_tree_item(self, parent_path, parent_widget, level=0):
        """
        Creates a single item (file or directory) in the tree view.
        """
        try:
            path = Path(parent_path)

            item_frame = ttkb.Frame(parent_widget)
            item_frame.pack(fill="x", pady=1)

            indent_frame = ttkb.Frame(item_frame)
            indent_frame.pack(side="left", padx=(level * 25, 0))

            tree_item = TreeItem(path)
            self.tree_items[str(path)] = tree_item

            chk_frame = ttkb.Frame(indent_frame)
            chk_frame.pack(side="left")

            chk = ttkb.Checkbutton(chk_frame, variable=tree_item.checked)
            chk.pack(side="left")

            if path.is_dir():
                try:
                    has_contents = any(True for _ in path.iterdir())
                    if has_contents:
                        btn = ttkb.Button(
                            chk_frame,
                            text="+",
                            width=3,
                            command=lambda p=path, f=item_frame: self.toggle_expand(
                                p, f
                            ),
                            bootstyle="light-outline",
                        )
                        btn.pack(side="left", padx=(5, 0))
                        tree_item.expand_button = btn
                    else:
                        ttkb.Label(chk_frame, width=3).pack(side="left", padx=(5, 0))
                except PermissionError:
                    ttkb.Label(chk_frame, text="X", width=3).pack(
                        side="left", padx=(5, 0)
                    )
            else:
                ttkb.Label(chk_frame, width=3).pack(side="left", padx=(5, 0))

            label_frame = ttkb.Frame(indent_frame)
            label_frame.pack(side="left", fill="x", expand=True, padx=(10, 0))

            icon = get_icon(path)

            item_label = ttkb.Label(
                label_frame,
                text=f"{icon} {path.name or str(path)}",
                font=("Segoe UI", 9),
            )
            item_label.pack(side="left")

            if path.is_file():
                try:
                    size = path.stat().st_size
                    size_str = format_file_size(size)
                    size_label = ttkb.Label(
                        label_frame,
                        text=f"({size_str})",
                        font=("Segoe UI", 8),
                    )
                    size_label.pack(side="left", padx=(10, 0))
                except:
                    pass

        except PermissionError:
            print(f"Permission denied: {parent_path}")
        except Exception as e:
            print(f"Error processing {parent_path}: {e}")

    def toggle_expand(self, path, parent_frame):
        """
        Expands or collapses a directory in the tree view, loading its contents if necessary.
        """
        tree_item = self.tree_items[str(path)]
        button = tree_item.expand_button
        if button is None:
            return

        if not tree_item.expanded:
            button.configure(text="-")
            container_frame = ttkb.Frame(parent_frame.master)
            container_frame.pack(fill="x", after=parent_frame)
            tree_item.container = container_frame

            try:
                items = sorted(
                    Path(path).iterdir(), key=lambda p: (p.is_file(), p.name.lower())
                )
                for item in items:
                    self.create_tree_item(
                        item,
                        container_frame,
                        level=len(Path(path).parts)
                        - len(Path(self.app.source_path.get()).parts)
                        + 1,
                    )
            except PermissionError:
                Messagebox.show_warning(
                    "Permission Denied", f"Cannot access contents of {path.name}"
                )

            tree_item.expanded = True
            tree_item.is_loaded = True
            self.app.config_manager.load_selections()
        else:
            button.configure(text="+")

            if hasattr(tree_item, "container") and tree_item.container:
                for widget in tree_item.container.winfo_children():
                    widget.destroy()
                tree_item.container.destroy()
                tree_item.container = None

            tree_item.expanded = False

    def select_all(self):
        """Selects all items in the tree view."""
        for tree_item in self.tree_items.values():
            tree_item.checked.set(True)

    def deselect_all(self):
        """Deselects all items in the tree view."""
        for tree_item in self.tree_items.values():
            tree_item.checked.set(False)

    def refresh_tree(self):
        """
        Refreshes the tree view, clearing the old view and building a new one based on the current source path.
        """
        if self.app.source_path.get():
            self.app.config_manager.save_selections()

        for widget in self.app.scrollable_frame.winfo_children():
            widget.destroy()
        self.tree_items.clear()

        if self.app.source_path.get():
            self.create_tree_item(self.app.source_path.get(), self.app.scrollable_frame)
            self.app.root.after(100, self.app.config_manager.load_selections)
