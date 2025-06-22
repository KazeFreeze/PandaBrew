import tkinter as tk
from tkinter import filedialog
import ttkbootstrap as ttkb
from ttkbootstrap.dialogs import Messagebox
from pathlib import Path

from .config_manager import ConfigManager
from .tree_view_manager import TreeViewManager
from .file_processor import FileProcessor
from .ui_components import UIComponents


class ModernCodeExtractorGUI:
    """
    The main class for the Code Extractor Pro application.
    This class initializes the GUI, manages user interactions, and orchestrates the different components of the application.
    """

    def __init__(self, root):
        """
        Initializes the main application window.

        Args:
            root (ttkb.Window): The root ttkbootstrap window.
        """
        self.root = root
        self.root.title("Code Extractor Pro")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)

        # Initialize managers and components, passing the app instance (self)
        self.config_manager = ConfigManager(self)
        self.config = self.config_manager.load_config()

        self.include_mode = tk.BooleanVar(value=True)
        self.filenames_only = tk.BooleanVar(value=False)
        self.source_path = tk.StringVar()
        self.output_path = tk.StringVar()

        # Initialize all managers before creating UI components that depend on them.
        self.tree_view_manager = TreeViewManager(self)
        self.file_processor = FileProcessor(self)

        self.ui_components = UIComponents(self)
        self.ui_components.create_modern_gui()

        # Load last used paths after the GUI is created
        if self.config.get("last_source"):
            self.source_path.set(self.config["last_source"])
            self.tree_view_manager.refresh_tree()
        if self.config.get("last_output"):
            self.output_path.set(self.config["last_output"])

    def browse_source(self):
        """
        Opens a dialog to select the source directory and updates the tree view.
        """
        folder = filedialog.askdirectory(title="Select Source Directory")
        if folder:
            self.source_path.set(folder)
            self.tree_view_manager.refresh_tree()
            self.config_manager.save_config()

    def browse_output(self):
        """
        Opens a dialog to select the output file path.
        """
        file = filedialog.asksaveasfilename(
            title="Save Extracted Code As",
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("All files", "*.*"),
            ],
        )
        if file:
            self.output_path.set(file)
            self.config_manager.save_config()

    def on_closing(self):
        """
        Handles the window closing event, saving the configuration before exiting.
        """
        self.config_manager.save_config()
        self.root.destroy()
