import tkinter as tk
from tkinter import filedialog, ttk
import ttkbootstrap as ttkb
from ttkbootstrap.dialogs import Messagebox
from pathlib import Path
import uuid
from typing import Dict, Any, Optional

from .config_manager import ConfigManager
from .tree_view_manager import TreeViewManager
from .file_processor import FileProcessor
from .ui_components import UIComponents


class ModernCodeExtractorGUI:
    """
    The main class for the Code Extractor Pro application.

    This class initializes the GUI, manages user interactions, and orchestrates
    the different components of the application with a browser-like tab interface.
    """

    def __init__(self, root: ttkb.Window):
        """
        Initializes the main application window.
        """
        self.root = root
        self.root.title("Code Extractor Pro")
        self.root.geometry("1100x750")
        self.root.minsize(900, 600)

        # Core components
        self.config_manager = ConfigManager(self)
        self.file_processor = FileProcessor(self)
        self.ui_components = UIComponents(self)

        # App state variables
        self.config: Dict[str, Any] = self.config_manager.load_app_state()
        self.include_mode = tk.BooleanVar(value=self.config.get("include_mode", True))
        self.filenames_only = tk.BooleanVar(
            value=self.config.get("filenames_only", False)
        )
        self.output_path = tk.StringVar(value=self.config.get("last_output", ""))
        self.tabs: Dict[str, Dict[str, Any]] = {}
        self.notebook: Optional[ttk.Notebook] = None  # Will be created by UIComponents

        # Initialize UI and events
        self.ui_components.create_main_layout()
        self.setup_event_bindings()
        self.load_tabs_from_config()

    def setup_event_bindings(self) -> None:
        """Centralized place to set up all major event bindings."""
        if self.notebook:
            self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

            def _on_mousewheel(event: tk.Event) -> None:
                active_tab = self.get_active_tab()
                if active_tab and active_tab.get("canvas"):
                    active_tab["canvas"].yview_scroll(
                        int(-1 * (event.delta / 120)), "units"
                    )

            self.notebook.bind("<MouseWheel>", _on_mousewheel)

    def add_new_tab(
        self, source_path: Optional[str] = None, select_tab: bool = True
    ) -> str:
        """
        Adds a new tab to the notebook.
        """
        tab_id = str(uuid.uuid4())
        content_frame = ttkb.Frame(self.notebook)

        tab_name = Path(source_path).name if source_path else "New Tab"
        self.notebook.add(content_frame, text=tab_name)

        tab_data = {
            "id": tab_id,
            "frame": content_frame,
            "source_path": tk.StringVar(value=source_path or ""),
            "tree_view_manager": TreeViewManager(self, tab_id),
            "scrollable_frame": None,
            "canvas": None,
        }
        self.tabs[tab_id] = tab_data

        self.ui_components.create_tab_ui(content_frame, tab_data)

        if select_tab:
            self.notebook.select(content_frame)

        if source_path:
            tab_data["tree_view_manager"].refresh_tree()

        return tab_id

    def close_tab_by_index(self, index: int) -> None:
        """Closes a specific tab using its display index."""
        try:
            tab_widget_path = self.notebook.tabs()[index]
            tab_widget = self.root.nametowidget(tab_widget_path)

            tab_id_to_close = None
            for tid, tdata in self.tabs.items():
                if tdata["frame"] == tab_widget:
                    tab_id_to_close = tid
                    break

            if tab_id_to_close:
                self.notebook.forget(index)
                del self.tabs[tab_id_to_close]

            if not self.notebook.tabs():
                self.add_new_tab()
        except (IndexError, tk.TclError) as e:
            print(f"Error closing tab at index {index}: {e}")

    def close_current_tab(self) -> None:
        """Closes the currently active tab."""
        if not self.notebook or not self.notebook.tabs():
            return

        try:
            current_tab_index = self.notebook.index(self.notebook.select())
            self.close_tab_by_index(current_tab_index)
        except tk.TclError:
            print("No tab selected to close.")

    def get_active_tab(self) -> Optional[Dict[str, Any]]:
        """Returns the data dictionary for the currently selected tab."""
        if not self.notebook or not self.notebook.tabs():
            return None
        try:
            selected_widget = self.root.nametowidget(self.notebook.select())
            for tab_data in self.tabs.values():
                if tab_data["frame"] == selected_widget:
                    return tab_data
        except (KeyError, tk.TclError):
            return None
        return None

    def on_tab_change(self, event: Optional[tk.Event] = None) -> None:
        """Updates window title when tab changes."""
        active_tab = self.get_active_tab()
        if active_tab and active_tab["source_path"].get():
            self.root.title(
                f"Code Extractor Pro - {Path(active_tab['source_path'].get()).name}"
            )
        else:
            self.root.title("Code Extractor Pro")

    def browse_source(self) -> None:
        """Opens a dialog to select the source directory for the active tab."""
        active_tab = self.get_active_tab()
        if not active_tab:
            return

        folder = filedialog.askdirectory(title="Select Source Directory")
        if folder:
            for tdata in self.tabs.values():
                if tdata["source_path"].get() == folder:
                    self.notebook.select(tdata["frame"])
                    return

            active_tab["source_path"].set(folder)
            tab_name = Path(folder).name
            self.notebook.tab(active_tab["frame"], text=tab_name)
            self.on_tab_change()
            active_tab["tree_view_manager"].refresh_tree()

    def browse_output(self) -> None:
        """Opens a dialog to select the output file path."""
        file = filedialog.asksaveasfilename(
            title="Save Extracted Code As",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if file:
            self.output_path.set(file)

    def load_tabs_from_config(self) -> None:
        """Loads the tabs that were open during the last session."""
        open_tabs = self.config.get("open_tabs", [])
        if open_tabs and isinstance(open_tabs, list):
            for i, path in enumerate(open_tabs):
                if isinstance(path, str) and Path(path).exists():
                    self.add_new_tab(source_path=path, select_tab=(i == 0))
        if not self.tabs:
            self.add_new_tab()

    def on_closing(self) -> None:
        """Saves configuration on exit."""
        self.config_manager.save_app_state()
        self.root.destroy()
