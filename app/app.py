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
    The main class for the PandaBrew application.
    """

    def __init__(self, root: ttkb.Window):
        """Initializes the main application window."""
        self.root = root
        self.root.title("PandaBrew")
        self.root.geometry("1100x750")
        self.root.minsize(900, 600)

        self.style = ttkb.Style()
        self.config_manager = ConfigManager(self)
        self.file_processor = ThreadedFileProcessor(self)
        self.ui_components = UIComponents(self)

        # Global app state variables
        self.config: Dict[str, Any] = self.config_manager.load_app_state()
        self.include_mode = tk.BooleanVar(value=self.config.get("include_mode", True))
        self.include_mode.trace_add("write", self.on_mode_change)
        self.filenames_only = tk.BooleanVar(value=self.config.get("filenames_only", False))
        self.show_excluded_in_structure = tk.BooleanVar(value=self.config.get("show_excluded_in_structure", True))

        self.tabs: Dict[str, Dict[str, Any]] = {}
        self.notebook: Optional[ttk.Notebook] = None
        self._bg_color_cache: Optional[str] = None
        self._after_id: Optional[str] = None

        # UI Widget references to be populated by UIComponents
        self.extract_btn: Optional[ttkb.Button] = None
        self.cancel_btn: Optional[ttkb.Button] = None
        self.progress: Optional[ttkb.Progressbar] = None
        self.status_label: Optional[ttkb.Label] = None

        # Initialize UI and events
        self.ui_components.create_main_layout()
        self.setup_event_bindings()
        self.load_tabs_from_config()
        self.on_tab_change()

    def setup_event_bindings(self) -> None:
        """Centralized place to set up all major event bindings."""
        if self.notebook:
            self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

    def on_mode_change(self, *args) -> None:
        """Callback for when the include/exclude mode changes."""
        active_tab = self.get_active_tab()
        if active_tab:
            active_tab["tree_view_manager"].refresh_tree()

    def show_filter_help(self) -> None:
        """Displays a dialog with help text for filter patterns."""
        pipeline_explanation = (
            "**Filter Precedence Pipeline**\n"
            "Filters are applied in the following order:\n\n"
            "1. **Manual Selections**: The initial set of files is determined by the "
            "checked items in the tree view and the 'Include/Exclude' mode.\n\n"
            "2. **Exclude Patterns**: Files matching these patterns are **removed** from the set.\n\n"
            "3. **Include Patterns**: Files matching these patterns are **added back** to the set, "
            "overriding any previous exclusions."
        )
        syntax_explanation = (
            "\n\n**Pattern Syntax**\n"
            "Patterns use glob-style matching, similar to .gitignore.\n\n"
            "- `*` matches everything\n"
            "- `?` matches any single character\n"
            "- `[seq]` matches any character in seq\n"
            "- `[!seq]` matches any character not in seq\n\n"
            "**Examples**\n"
            "- `*.py`: Matches all Python files.\n"
            "- `src/*`: Matches all files in the `src` directory.\n"
            "- `__pycache__/`: Matches the pycache directory.\n"
        )
        help_text = pipeline_explanation + syntax_explanation
        Messagebox.ok(help_text, title="Filter Help", parent=self.root)

    def add_new_tab(
        self,
        source_path: Optional[str] = None,
        output_path: Optional[str] = None,
        include_patterns: str = "",
        exclude_patterns: str = "",
        select_tab: bool = True,
    ) -> str:
        """Adds a new tab to the notebook."""
        tab_id = str(uuid.uuid4())
        content_frame = ttkb.Frame(self.notebook, style="primary.TFrame")
        tab_name = Path(source_path).name if source_path else "New Tab"
        if not self.notebook: return ""
        self.notebook.add(content_frame, text=tab_name)

        tab_data = {
            "id": tab_id, "frame": content_frame,
            "source_path": tk.StringVar(value=source_path or ""),
            "output_path": tk.StringVar(value=output_path or ""),
            "tree_view_manager": TreeViewManager(self, tab_id),
            "include_patterns_text": None, "exclude_patterns_text": None,
            "scrollable_frame": None, "canvas": None,
        }
        self.tabs[tab_id] = tab_data
        self.ui_components.create_tab_ui(content_frame, tab_data)

        if tab_data["include_patterns_text"]:
            tab_data["include_patterns_text"].insert("1.0", include_patterns)
        if tab_data["exclude_patterns_text"]:
            tab_data["exclude_patterns_text"].insert("1.0", exclude_patterns)

        if select_tab: self.notebook.select(content_frame)
        if source_path: tab_data["tree_view_manager"].refresh_tree()
        self.on_tab_change()
        return tab_id

    def close_tab_by_index(self, index: int) -> None:
        """Closes a specific tab using its display index."""
        if not self.notebook: return
        try:
            tab_widget_path = self.notebook.tabs()[index]
            tab_widget = self.root.nametowidget(tab_widget_path)
            tab_id_to_close = next((tid for tid, tdata in self.tabs.items() if tdata["frame"] == tab_widget), None)
            if tab_id_to_close:
                self.notebook.forget(index)
                del self.tabs[tab_id_to_close]
            if not self.notebook.tabs(): self.add_new_tab()
        except (IndexError, tk.TclError) as e:
            print(f"Error closing tab at index {index}: {e}")
        finally:
            self.on_tab_change()

    def close_current_tab(self) -> None:
        """Closes the currently active tab."""
        if not self.notebook or not self.notebook.tabs(): return
        try:
            self.close_tab_by_index(self.notebook.index(self.notebook.select()))
        except tk.TclError: pass

    def get_active_tab(self) -> Optional[Dict[str, Any]]:
        """Returns the data dictionary for the currently selected tab."""
        if not self.notebook or not self.notebook.tabs(): return None
        try:
            selected_widget = self.root.nametowidget(self.notebook.select())
            return next((tdata for tdata in self.tabs.values() if tdata["frame"] == selected_widget), None)
        except (KeyError, tk.TclError): return None

    def on_tab_change(self, event: Optional[tk.Event] = None) -> None:
        self.refresh_active_tab_ui()

    def refresh_active_tab_ui(self) -> None:
        active_tab = self.get_active_tab()
        if active_tab and active_tab["source_path"].get():
            self.root.title(f"PandaBrew - {Path(active_tab['source_path'].get()).name}")
        else:
            self.root.title("PandaBrew")
        self._refresh_canvas_style_debounced()

    def _refresh_canvas_style_debounced(self) -> None:
        if self._after_id: self.root.after_cancel(self._after_id)
        self._after_id = self.root.after(15, self._perform_canvas_refresh)

    def _perform_canvas_refresh(self) -> None:
        self._after_id = None
        active_tab = self.get_active_tab()
        if not (active_tab and active_tab.get("canvas")): return
        try:
            if self._bg_color_cache is None: self._bg_color_cache = self.style.colors.get("bg") or "#2c3e50"
            active_tab["canvas"].update_idletasks()
            active_tab["canvas"].configure(bg=self._bg_color_cache)
        except tk.TclError: pass

    def browse_source(self) -> None:
        active_tab = self.get_active_tab()
        if not active_tab:
            self.add_new_tab(select_tab=True)
            active_tab = self.get_active_tab()
            if not active_tab: return
        folder = filedialog.askdirectory(title="Select Source Directory")
        if not folder: return
        for tdata in self.tabs.values():
            if tdata["source_path"].get() == folder:
                if self.notebook: self.notebook.select(tdata["frame"])
                return
        active_tab["source_path"].set(folder)
        if self.notebook: self.notebook.tab(active_tab["frame"], text=Path(folder).name)
        self.on_tab_change()
        active_tab["tree_view_manager"].refresh_tree()

    def browse_output(self) -> None:
        active_tab = self.get_active_tab()
        if not active_tab: return
        file = filedialog.asksaveasfilename(title="Save As", defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file: active_tab["output_path"].set(file)

    def load_tabs_from_config(self) -> None:
        open_tabs = self.config.get("open_tabs", [])
        active_tab_source = self.config.get("active_tab_source")
        if open_tabs and isinstance(open_tabs, list):
            for tab_info in open_tabs:
                if isinstance(tab_info, dict):
                    source = tab_info.get("source")
                    if source and Path(source).exists():
                        self.add_new_tab(
                            source_path=source,
                            output_path=tab_info.get("output"),
                            include_patterns=tab_info.get("include_patterns", ""),
                            exclude_patterns=tab_info.get("exclude_patterns", ""),
                            select_tab=False,
                        )
            if active_tab_source:
                for tab_data in self.tabs.values():
                    if tab_data["source_path"].get() == active_tab_source:
                        if self.notebook: self.notebook.select(tab_data["frame"])
                        break
        if not self.tabs: self.add_new_tab()
        self.refresh_active_tab_ui()

    def set_ui_processing_state(self, is_processing: bool) -> None:
        if is_processing:
            if self.extract_btn: self.extract_btn.config(state="disabled")
            if self.cancel_btn: self.cancel_btn.pack(side="left", padx=(0, 10))
        else:
            if self.extract_btn: self.extract_btn.config(state="normal")
            if self.cancel_btn: self.cancel_btn.pack_forget()

    def on_closing(self) -> None:
        if self.file_processor.is_processing:
            if Messagebox.okcancel("Processing in Progress", "An extraction is currently running. Are you sure you want to quit?", parent=self.root) == "Cancel":
                return
            self.file_processor.cancel_processing()
            if self.file_processor.processing_thread:
                self.file_processor.processing_thread.join(timeout=0.5)
        self.config_manager.save_app_state()
        self.root.destroy()
