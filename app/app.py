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

        # --- Global (non-tab-specific) components ---
        self.config_manager = ConfigManager(self)
        self.config = self.config_manager.load_config()
        self.file_processor = FileProcessor(self)

        # Global options that will be linked to UI controls in each tab
        self.include_mode = tk.BooleanVar(value=self.config.get("include_mode", True))
        self.filenames_only = tk.BooleanVar(
            value=self.config.get("filenames_only", False)
        )
        self.output_path = tk.StringVar(value=self.config.get("last_output", ""))

        # --- Tab management ---
        self.tabs = {}  # Dictionary to hold data for each tab
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

        # This will be created by UIComponents
        self.ui_components = UIComponents(self)
        self.ui_components.create_main_layout()

        self.load_tabs_from_config()

    def add_new_tab(self, source_path=None, select_tab=True):
        """
        Adds a new tab to the notebook, either for a specific path or as a blank tab.
        """
        tab_id = str(uuid.uuid4())
        tab_frame = ttkb.Frame(self.notebook)
        self.notebook.add(
            tab_frame, text=Path(source_path).name if source_path else "New Tab"
        )

        # Each tab gets its own set of variables and managers
        tab_data = {
            "id": tab_id,
            "frame": tab_frame,
            "source_path": tk.StringVar(value=source_path if source_path else ""),
            "tree_view_manager": TreeViewManager(self, tab_id),
            "scrollable_frame": None,  # Will be created by UIComponents
            "canvas": None,  # Will be created by UIComponents
        }
        self.tabs[tab_id] = tab_data

        # Create the UI inside the new tab's frame
        self.ui_components.create_tab_ui(tab_frame, tab_data)

        if select_tab:
            # Select the newly created tab
            self.notebook.select(tab_frame)

        if source_path:
            # Refresh the tree to show the directory contents
            tab_data["tree_view_manager"].refresh_tree()

        return tab_id

    def close_current_tab(self):
        """Closes the currently active tab."""
        if not self.notebook.tabs():
            return

        selected_tab_widget = self.root.nametowidget(self.notebook.select())

        tab_id_to_remove = None
        for tid, tdata in self.tabs.items():
            if tdata["frame"] == selected_tab_widget:
                tab_id_to_remove = tid
                break

        if tab_id_to_remove:
            # Save selections before closing
            self.config_manager.save_selections(self.tabs[tab_id_to_remove])
            self.notebook.forget(selected_tab_widget)
            del self.tabs[tab_id_to_remove]

        # If no tabs are left, add a fresh one
        if not self.notebook.tabs():
            self.add_new_tab()

    def get_active_tab(self):
        """
        Returns the data dictionary for the currently selected tab.
        """
        if not self.notebook.tabs():
            return None

        try:
            selected_tab_widget = self.root.nametowidget(self.notebook.select())
            for tab_data in self.tabs.values():
                if tab_data["frame"] == selected_tab_widget:
                    return tab_data
        except KeyError:
            # This can happen briefly during tab closing
            return None
        return None

    def on_tab_change(self, event):
        """
        Handles actions to perform when the active tab is changed.
        """
        active_tab = self.get_active_tab()
        if active_tab and active_tab["source_path"].get():
            self.root.title(
                f"Code Extractor Pro - {Path(active_tab['source_path'].get()).name}"
            )
        else:
            self.root.title("Code Extractor Pro")

    def browse_source(self):
        """
        Opens a dialog to select the source directory for the active tab.
        """
        active_tab = self.get_active_tab()
        if not active_tab:
            return

        folder = filedialog.askdirectory(title="Select Source Directory")
        if folder:
            # Check if this directory is already open in another tab
            for tab_data in self.tabs.values():
                if tab_data["source_path"].get() == folder:
                    Messagebox.show_warning(
                        "Directory Open",
                        f"The directory '{Path(folder).name}' is already open in another tab.",
                    )
                    self.notebook.select(tab_data["frame"])
                    return

            active_tab["source_path"].set(folder)
            self.notebook.tab(active_tab["frame"], text=Path(folder).name)
            self.on_tab_change(None)  # Update window title
            active_tab["tree_view_manager"].refresh_tree()

    def browse_output(self):
        """
        Opens a dialog to select the output file path (global setting).
        """
        file = filedialog.asksaveasfilename(
            title="Save Extracted Code As",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if file:
            self.output_path.set(file)

    def load_tabs_from_config(self):
        """
        Loads the tabs that were open during the last session.
        This is now hardened against corrupted config data.
        """
        open_tabs = self.config.get("open_tabs", [])

        # Add checks to ensure open_tabs is a list and its elements are strings
        if open_tabs and isinstance(open_tabs, list):
            for i, path in enumerate(open_tabs):
                # FIX: Check if the path is a string before trying to use it.
                # This prevents the crash reported in the traceback.
                if isinstance(path, str) and Path(path).exists():
                    self.add_new_tab(source_path=path, select_tab=(i == 0))

        # If no valid tabs were loaded (or list was empty/invalid), create a default one
        if not self.tabs:
            self.add_new_tab()

    def on_closing(self):
        """
        Handles the window closing event, saving the configuration before exiting.
        """
        self.config_manager.save_config()
        self.root.destroy()
