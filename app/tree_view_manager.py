import tkinter as tk
import ttkbootstrap as ttkb
from pathlib import Path
from utils.helpers import format_file_size
from typing import Optional, Dict, Any, Set, List
from functools import partial

# Define consistent fonts for the terminal theme
TERMINAL_FONT = ("Cascadia Code", 9)
TREE_FONT = ("Consolas", 10)
TREE_FONT_BOLD = ("Consolas", 10, "bold")
ITALIC_FONT = ("Cascadia Code", 8, "italic")
PAGE_SIZE = 100  # Number of items to load at a time

class TreeItem:
    """Represents a visual item in the tree view."""
    def __init__(self, path: Path):
        self.path = path
        self.expanded = False
        self.checked = tk.BooleanVar()
        self.widget: Optional[ttkb.Frame] = None
        self.container: Optional[ttkb.Frame] = None
        self.expander_label: Optional[ttkb.Label] = None
        self.child_paths: Optional[List[Path]] = None

class TreeViewManager:
    """Manages the file and directory tree view for a single tab."""
    def __init__(self, app_instance, tab_id: str):
        self.app = app_instance
        self.tab_id = tab_id
        self.tree_items: Dict[str, TreeItem] = {}
        self.checked_paths: Set[str] = set()

    def get_tab_data(self) -> Optional[Dict[str, Any]]:
        return self.app.tabs.get(self.tab_id)

    def _populate_node_children(self, parent_item: TreeItem, offset: int = 0):
        """Builds and displays one page of children for a given parent node."""
        if not parent_item.container or parent_item.child_paths is None:
            return

        start = offset
        end = offset + PAGE_SIZE
        paths_to_render = parent_item.child_paths[start:end]

        for path in paths_to_render:
            self.create_tree_item_widget(path, parent_item.container)

        # If there are more items to load, add a "Load More" button
        if end < len(parent_item.child_paths):
            load_more_button = ttkb.Button(
                parent_item.container,
                text=f"Load More ({len(parent_item.child_paths) - end} remaining)...",
                bootstyle="link",
                command=partial(self._load_more, parent_item, load_more_button, end)
            )
            load_more_button.pack(fill="x", padx=20, pady=5)

    def _load_more(self, parent_item: TreeItem, button_to_destroy: ttkb.Button, new_offset: int):
        """Called by the 'Load More' button to render the next page of items."""
        button_to_destroy.destroy()
        self._populate_node_children(parent_item, offset=new_offset)

    def create_tree_item_widget(self, path: Path, parent_widget: ttkb.Frame):
        """Creates the UI widget for a single item in the tree."""
        path_str = str(path)
        if path_str in self.tree_items and self.tree_items[path_str].widget:
            return

        item_frame = ttkb.Frame(parent_widget)
        item_frame.pack(fill="x")

        # Calculate indentation based on depth
        tab_data = self.get_tab_data()
        source_path = Path(tab_data["source_path"].get()) if tab_data and tab_data["source_path"].get() else None
        depth = len(path.parts) - len(source_path.parts) if source_path else 0
        indent = "    " * depth
        ttkb.Label(item_frame, text=indent).pack(side="left")

        tree_item = self.tree_items.get(path_str) or TreeItem(path)
        tree_item.widget = item_frame

        is_expandable = path.is_dir()
        expander_text = "[+]" if is_expandable else "   "
        expander = ttkb.Label(item_frame, text=expander_text, font=TREE_FONT_BOLD, foreground=self.app.style.colors.get("info"), width=3)
        if is_expandable:
            expander.bind("<Button-1>", lambda e, p=path: self.toggle_expand(p))
        expander.pack(side="left")
        tree_item.expander_label = expander

        tree_item.checked.set(path_str in self.checked_paths)
        chk = ttkb.Checkbutton(item_frame, variable=tree_item.checked, command=lambda p=path_str, v=tree_item.checked: self.on_item_check(p, v), bootstyle="info-square-toggle")
        chk.pack(side="left")
        self.tree_items[path_str] = tree_item

        icon = "📁" if path.is_dir() else "📄"
        name_label = ttkb.Label(item_frame, text=f"{icon} {path.name}", compound="left", font=TERMINAL_FONT)
        name_label.pack(side="left")

        if is_expandable:
            name_label.bind("<Button-1>", lambda e, p=path: self.toggle_expand(p))

        if tab_data and "bind_scroll_handler" in tab_data:
            tab_data["bind_scroll_handler"](item_frame)

    def toggle_expand(self, path: Path):
        """Expands or collapses a directory, loading its contents on first expansion."""
        path_str = str(path)
        tree_item = self.tree_items.get(path_str)
        if not tree_item or not tree_item.expander_label: return

        if not tree_item.expanded:
            tree_item.expander_label.config(text="[-]")
            if not tree_item.container:
                tree_item.container = ttkb.Frame(tree_item.widget.master)
                tree_item.container.pack(fill="x", after=tree_item.widget)
                try:
                    if tree_item.child_paths is None:
                        tree_item.child_paths = sorted(list(path.iterdir()), key=lambda p: (p.is_file(), p.name.lower()))
                    self._populate_node_children(tree_item, offset=0)
                except Exception as e:
                    print(f"Error expanding {path}: {e}")
            tree_item.expanded = True
        else:
            tree_item.expander_label.config(text="[+]")
            if tree_item.container:
                for child in tree_item.container.winfo_children():
                    child.destroy()
            tree_item.expanded = False

    def on_item_check(self, path_str: str, var: tk.BooleanVar):
        is_checked = var.get()
        if is_checked:
            self.checked_paths.add(path_str)
        else:
            self.checked_paths.discard(path_str)

    def select_all(self):
        tab_data = self.get_tab_data()
        if not (tab_data and tab_data["source_path"].get()): return
        source_path = Path(tab_data["source_path"].get())
        try:
            self.checked_paths = {str(p) for p in source_path.rglob("*")}
            self.checked_paths.add(str(source_path))
            for item in self.tree_items.values():
                item.checked.set(True)
        except Exception as e:
            print(f"Error during select all: {e}")

    def deselect_all(self):
        self.checked_paths.clear()
        for item in self.tree_items.values():
            item.checked.set(False)

    def refresh_tree(self):
        """Refreshes the tree view, clearing the old view and building the root."""
        tab_data = self.get_tab_data()
        if not (tab_data and tab_data.get("scrollable_frame")): return

        for widget in tab_data["scrollable_frame"].winfo_children():
            widget.destroy()
        self.tree_items.clear()

        source_path_str = tab_data["source_path"].get()
        if source_path_str:
            source_path = Path(source_path_str)
            if source_path.exists() and source_path.is_dir():
                self.app.config_manager.load_selections(tab_data)
                self.create_tree_item_widget(source_path, tab_data["scrollable_frame"])
                self.toggle_expand(source_path)
            else:
                ttkb.Label(tab_data["scrollable_frame"], text=f"Path not found: {source_path_str}", bootstyle="danger").pack(pady=10)
