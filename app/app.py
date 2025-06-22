import tkinter as tk
from tkinter import filedialog, ttk
import ttkbootstrap as ttkb
from ttkbootstrap.dialogs import Messagebox
from pathlib import Path
import uuid

from .config_manager import ConfigManager
from .tree_view_manager import TreeViewManager
from .file_processor import FileProcessor
from .ui_components import UIComponents


class ModernCodeExtractorGUI:
    """
    The main class for the Code Extractor Pro application.
    This class initializes the GUI, manages user interactions, and orchestrates
    the different components of the application, now with a tabbed interface.
    """

    def __init__(self, root):
        """
        Initializes the main application window.
        """
        self.root = root
        self.root.title("Code Extractor Pro")
        self.root.geometry("1100x750")
        self.root.minsize(800, 600)

        self.config_manager = ConfigManager(self)
        self.config = self.config_manager.load_config()
        self.file_processor = FileProcessor(self)

        self.include_mode = tk.BooleanVar(value=self.config.get("include_mode", True))
        self.filenames_only = tk.BooleanVar(
            value=self.config.get("filenames_only", False)
        )
        self.output_path = tk.StringVar(value=self.config.get("last_output", ""))

        # --- Tab management ---
        self.tabs = {}

        # NEW: A frame to contain the notebook and the '+' button for a cleaner layout
        tab_container = ttkb.Frame(self.root)
        tab_container.pack(expand=True, fill="both", padx=10, pady=(10, 0))

        self.notebook = ttk.Notebook(tab_container)
        self.notebook.pack(side="left", expand=True, fill="both")

        # NEW: Add new tab button `+` next to the tabs
        add_tab_button = ttkb.Button(
            tab_container,
            text="+",
            width=3,
            command=self.add_new_tab,
            bootstyle="secondary",
        )
        add_tab_button.pack(side="left", anchor="n", padx=(5, 0), pady=2)

        self.ui_components = UIComponents(self)
        self.ui_components.create_main_layout()

        self.setup_event_bindings()
        self.load_tabs_from_config()

    def setup_event_bindings(self):
        """Centralized place to set up all major event bindings."""
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

        # NEW: Right-click menu for closing tabs
        self.tab_context_menu = tk.Menu(self.root, tearoff=0)
        self.tab_context_menu.add_command(
            label="Close Tab", command=self.close_current_tab
        )
        self.notebook.bind("<Button-3>", self.show_tab_context_menu)

        # NEW: Robust mousewheel scrolling that targets the active canvas
        def _on_mousewheel(event):
            active_tab = self.get_active_tab()
            if active_tab and active_tab.get("canvas"):
                active_tab["canvas"].yview_scroll(
                    int(-1 * (event.delta / 120)), "units"
                )

        # Bind scrolling to the entire notebook area for better usability
        self.notebook.bind("<MouseWheel>", _on_mousewheel)

    def add_new_tab(self, source_path=None, select_tab=True):
        """
        Adds a new tab to the notebook.
        """
        tab_id = str(uuid.uuid4())
        tab_frame = ttkb.Frame(self.notebook)
        tab_name = Path(source_path).name if source_path else "New Tab"
        self.notebook.add(tab_frame, text=f" {tab_name} ")  # Add padding to text

        tab_data = {
            "id": tab_id,
            "frame": tab_frame,
            "source_path": tk.StringVar(value=source_path or ""),
            "tree_view_manager": TreeViewManager(self, tab_id),
            "scrollable_frame": None,
            "canvas": None,
        }
        self.tabs[tab_id] = tab_data

        self.ui_components.create_tab_ui(tab_frame, tab_data)

        if select_tab:
            self.notebook.select(tab_frame)

        if source_path:
            tab_data["tree_view_manager"].refresh_tree()

        return tab_id

    def close_current_tab(self):
        """Closes the currently active tab (determined by right-click)."""
        if not self.notebook.tabs():
            return

        selected_tab_id = self.notebook.select()
        if not selected_tab_id:
            return

        selected_tab_widget = self.root.nametowidget(selected_tab_id)

        tab_id_to_remove = None
        for tid, tdata in self.tabs.items():
            if tdata["frame"] == selected_tab_widget:
                tab_id_to_remove = tid
                break

        if tab_id_to_remove:
            self.config_manager.save_selections(self.tabs[tab_id_to_remove])
            self.notebook.forget(selected_tab_widget)
            del self.tabs[tab_id_to_remove]

        if not self.notebook.tabs():
            self.add_new_tab()

    def get_active_tab(self):
        """Returns the data dictionary for the currently selected tab."""
        if not self.notebook.tabs():
            return None
        try:
            selected_widget = self.root.nametowidget(self.notebook.select())
            for tab_data in self.tabs.values():
                if tab_data["frame"] == selected_widget:
                    return tab_data
        except (KeyError, tk.TclError):
            return None
        return None

    def on_tab_change(self, event):
        """Updates window title when tab changes."""
        active_tab = self.get_active_tab()
        if active_tab and active_tab["source_path"].get():
            self.root.title(
                f"Code Extractor Pro - {Path(active_tab['source_path'].get()).name}"
            )
        else:
            self.root.title("Code Extractor Pro")

    def show_tab_context_menu(self, event):
        """Shows a context menu on right-click to close a tab."""
        try:
            tab_index = self.notebook.index(f"@{event.x},{event.y}")
            self.notebook.select(tab_index)
            self.tab_context_menu.post(event.x_root, event.y_root)
        except tk.TclError:
            pass  # Click was not on a tab

    def browse_source(self):
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
            self.notebook.tab(active_tab["frame"], text=f" {Path(folder).name} ")
            self.on_tab_change(None)
            active_tab["tree_view_manager"].refresh_tree()

    def browse_output(self):
        """Opens a dialog to select the output file path."""
        file = filedialog.asksaveasfilename(
            title="Save Extracted Code As",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if file:
            self.output_path.set(file)

    def load_tabs_from_config(self):
        """Loads the tabs that were open during the last session."""
        open_tabs = self.config.get("open_tabs", [])
        if open_tabs and isinstance(open_tabs, list):
            for i, path in enumerate(open_tabs):
                if isinstance(path, str) and Path(path).exists():
                    self.add_new_tab(source_path=path, select_tab=(i == 0))
        if not self.tabs:
            self.add_new_tab()

    def on_closing(self):
        """Saves configuration on exit."""
        self.config_manager.save_config()
        self.root.destroy()
