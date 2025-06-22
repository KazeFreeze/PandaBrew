import tkinter as tk
from tkinter import filedialog, ttk
import ttkbootstrap as ttkb
from ttkbootstrap.dialogs import Messagebox
from pathlib import Path
import uuid
from typing import Dict, Any, Optional

from .config_manager import ConfigManager
from .tree_view_manager import TreeViewManager
from .threaded_file_processor import ThreadedFileProcessor
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

        # Initialize ttkbootstrap style object for custom theming
        self.style = ttkb.Style()

        # Core components
        self.config_manager = ConfigManager(self)
        self.file_processor = ThreadedFileProcessor(self)
        self.ui_components = UIComponents(self)

        # App state variables
        self.config: Dict[str, Any] = self.config_manager.load_app_state()
        self.include_mode = tk.BooleanVar(value=self.config.get("include_mode", True))
        self.filenames_only = tk.BooleanVar(
            value=self.config.get("filenames_only", False)
        )
        self.tabs: Dict[str, Dict[str, Any]] = {}
        self.notebook: Optional[ttk.Notebook] = None

        # --- FIX IMPLEMENTATION START ---
        # Cache for background color and debounce ID for canvas refresh
        self._bg_color_cache: Optional[str] = None
        self._after_id: Optional[str] = None
        # --- FIX IMPLEMENTATION END ---

        # UI Widget references to be populated by UIComponents
        self.extract_btn: Optional[ttkb.Button] = None
        self.cancel_btn: Optional[ttkb.Button] = None
        self.progress: Optional[ttkb.Progressbar] = None
        self.status_label: Optional[ttkb.Label] = None

        # Initialize UI and events
        self.ui_components.create_main_layout()
        self.setup_event_bindings()
        self.load_tabs_from_config()
        self.on_tab_change()  # Set initial title and canvas style

    def setup_event_bindings(self) -> None:
        """Centralized place to set up all major event bindings."""
        if self.notebook:
            self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

    def add_new_tab(
        self,
        source_path: Optional[str] = None,
        output_path: Optional[str] = None,
        select_tab: bool = True,
    ) -> str:
        """Adds a new tab to the notebook."""
        tab_id = str(uuid.uuid4())
        content_frame = ttkb.Frame(self.notebook, style="primary.TFrame")

        tab_name = Path(source_path).name if source_path else "New Tab"
        if not self.notebook:
            print("Error: Notebook not initialized.")
            return ""

        self.notebook.add(content_frame, text=tab_name)

        tab_data = {
            "id": tab_id,
            "frame": content_frame,
            "source_path": tk.StringVar(value=source_path or ""),
            "output_path": tk.StringVar(value=output_path or ""),
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

        self.on_tab_change()
        return tab_id

    def close_tab_by_index(self, index: int) -> None:
        """Closes a specific tab using its display index."""
        if not self.notebook:
            return
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
        finally:
            self.on_tab_change()

    def close_current_tab(self) -> None:
        """Closes the currently active tab."""
        if not self.notebook or not self.notebook.tabs():
            return

        try:
            current_tab_index = self.notebook.index(self.notebook.select())
            self.close_tab_by_index(current_tab_index)
        except tk.TclError:
            pass

    def get_active_tab(self) -> Optional[Dict[str, Any]]:
        """Returns the data dictionary for the currently selected tab."""
        if not self.notebook or not self.notebook.tabs():
            return None
        try:
            selected_widget_path = self.notebook.select()
            if not selected_widget_path:
                return None
            selected_widget = self.root.nametowidget(selected_widget_path)
            for tab_data in self.tabs.values():
                if tab_data["frame"] == selected_widget:
                    return tab_data
        except (KeyError, tk.TclError):
            return None
        return None

    def on_tab_change(self, event: Optional[tk.Event] = None) -> None:
        """Handles events when the active tab changes."""
        # --- FIX IMPLEMENTATION START ---
        # Centralized method to handle all post-tab-change UI updates
        self.refresh_active_tab_ui()
        # --- FIX IMPLEMENTATION END ---

    # --- FIX IMPLEMENTATION START ---
    def refresh_active_tab_ui(self) -> None:
        """
        Updates the UI based on the currently active tab. This includes the
        window title and refreshing the canvas style to prevent artifacts.
        """
        active_tab = self.get_active_tab()

        # Update window title
        if active_tab and active_tab["source_path"].get():
            self.root.title(
                f"Code Extractor Pro - {Path(active_tab['source_path'].get()).name}"
            )
        else:
            self.root.title("Code Extractor Pro")

        # Refresh canvas style to prevent rendering artifacts
        self._refresh_canvas_style_debounced()

    def _refresh_canvas_style_debounced(self) -> None:
        """
        Refreshes the active canvas's background color after a short delay.
        This is debounced to prevent rapid, unnecessary updates when switching
        tabs quickly. This helps fix rendering glitches with the mica style.
        """
        if self._after_id:
            self.root.after_cancel(self._after_id)

        self._after_id = self.root.after(15, self._perform_canvas_refresh)

    def _perform_canvas_refresh(self) -> None:
        """The actual logic to refresh the canvas style."""
        self._after_id = None
        active_tab = self.get_active_tab()
        if not (active_tab and active_tab.get("canvas")):
            return

        canvas = active_tab["canvas"]

        if self._bg_color_cache is None:
            self._bg_color_cache = self.style.colors.get("bg") or "#2c3e50"

        try:
            canvas.update_idletasks()
            canvas.configure(bg=self._bg_color_cache)
        except tk.TclError:
            pass  # Widget might have been destroyed

    # --- FIX IMPLEMENTATION END ---

    def browse_source(self) -> None:
        """Opens a dialog to select the source directory for the active tab."""
        active_tab = self.get_active_tab()
        if not active_tab:
            self.add_new_tab(select_tab=True)
            active_tab = self.get_active_tab()
            if not active_tab:
                Messagebox.show_error(
                    "Error", "Could not create a new tab.", parent=self.root
                )
                return

        folder = filedialog.askdirectory(title="Select Source Directory")
        if folder:
            for tdata in self.tabs.values():
                if tdata["source_path"].get() == folder:
                    if self.notebook:
                        self.notebook.select(tdata["frame"])
                    return

            active_tab["source_path"].set(folder)
            tab_name = Path(folder).name
            if self.notebook:
                self.notebook.tab(active_tab["frame"], text=tab_name)
            self.on_tab_change()
            active_tab["tree_view_manager"].refresh_tree()

    def browse_output(self) -> None:
        """Opens a dialog to select the output file path for the active tab."""
        active_tab = self.get_active_tab()
        if not active_tab:
            Messagebox.show_error(
                "Error", "No active tab to set output path for.", parent=self.root
            )
            return

        file = filedialog.asksaveasfilename(
            title="Save Extracted Code As",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if file:
            active_tab["output_path"].set(file)

    def load_tabs_from_config(self) -> None:
        """Loads the tabs that were open during the last session."""
        open_tabs = self.config.get("open_tabs", [])
        active_tab_source = self.config.get("active_tab_source")

        if open_tabs and isinstance(open_tabs, list):
            for tab_info in open_tabs:
                if isinstance(tab_info, dict):
                    source = tab_info.get("source")
                    output = tab_info.get("output")
                    if source and Path(source).exists():
                        self.add_new_tab(
                            source_path=source,
                            output_path=output,
                            select_tab=False,
                        )

            if active_tab_source:
                for tab_data in self.tabs.values():
                    if tab_data["source_path"].get() == active_tab_source:
                        if self.notebook:
                            self.notebook.select(tab_data["frame"])
                            break

        if not self.tabs:
            self.add_new_tab()

        self.refresh_active_tab_ui()

    def set_ui_processing_state(self, is_processing: bool) -> None:
        """Toggles the state of UI controls during processing."""
        if is_processing:
            if self.extract_btn:
                self.extract_btn.config(state="disabled")
            if self.cancel_btn:
                self.cancel_btn.pack(side="left", padx=(0, 10))
        else:
            if self.extract_btn:
                self.extract_btn.config(state="normal")
            if self.cancel_btn:
                self.cancel_btn.pack_forget()

    def on_closing(self) -> None:
        """
        Saves configuration on exit and cancels any running process.
        """
        if self.file_processor.is_processing:
            if (
                Messagebox.okcancel(
                    "Processing in Progress",
                    "An extraction is currently running. Are you sure you want to quit?\nThe process will be cancelled.",
                    parent=self.root,
                    title="Confirm Exit",
                )
                == "Cancel"
            ):
                return

            self.file_processor.cancel_processing()
            if self.file_processor.processing_thread:
                self.file_processor.processing_thread.join(timeout=0.5)

        self.config_manager.save_app_state()
        self.root.destroy()
