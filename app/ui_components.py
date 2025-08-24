import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttkb
from ttkbootstrap.scrolled import ScrolledText
from pathlib import Path
from typing import Dict, Any, Callable

# Define a consistent font for the terminal theme
TERMINAL_FONT = ("Cascadia Code", 9)
TERMINAL_FONT_BOLD = ("Cascadia Code", 9, "bold")
TREE_FONT = ("Consolas", 10)


class UIComponents:
    """
    Manages the creation and layout of all the UI components.
    """

    def __init__(self, app_instance):
        self.app = app_instance
        self.notebook = None
        self._configure_styles()

    def _configure_styles(self) -> None:
        """Configures custom ttk styles for the terminal theme."""
        style = self.app.style
        style.configure(".", font=TERMINAL_FONT)
        style.configure("TLabel", font=TERMINAL_FONT)
        style.configure("TButton", font=TERMINAL_FONT_BOLD)
        style.configure("Toolbutton", font=TERMINAL_FONT)
        style.configure("TCheckbutton", font=TERMINAL_FONT)
        style.configure("TRadiobutton", font=TERMINAL_FONT)
        style.configure("TEntry", font=TERMINAL_FONT)
        style.configure("TLabelframe", padding=15)
        style.configure("TLabelframe.Label", font=TERMINAL_FONT_BOLD, foreground=style.colors.get("info"))
        style.configure("TNotebook.Tab", font=TERMINAL_FONT, padding=[10, 5])
        style.map("TNotebook.Tab", font=[("selected", TERMINAL_FONT_BOLD)], foreground=[("selected", "white"), ("!selected", style.colors.get("info"))], background=[("selected", style.colors.get("bg")), ("!selected", "#404040")])

    def create_main_layout(self) -> None:
        """Creates the main layout of the application."""
        self.app.root.configure(bg=self.app.style.colors.get("bg"))
        top_frame = ttkb.Frame(self.app.root)
        top_frame.pack(expand=True, fill="both", padx=10, pady=(10, 0))
        self.notebook = ttk.Notebook(top_frame)
        self.app.notebook = self.notebook
        self.notebook.pack(side="left", expand=True, fill="both")
        self._create_tab_control_buttons(top_frame)
        control_container = ttkb.Frame(self.app.root, padding=(10, 10))
        control_container.pack(fill="x", side="bottom")
        self.create_control_buttons(control_container)

    def _create_tab_control_buttons(self, parent: ttkb.Frame) -> None:
        """Creates the '+', 'x', and '?' buttons for tab management and help."""
        button_frame = ttkb.Frame(parent)
        button_frame.pack(side="left", anchor="n", fill="y", padx=(2, 0), pady=2)

        add_tab_button = ttkb.Button(button_frame, text="+", width=2, command=self.app.add_new_tab, bootstyle="success-outline")
        add_tab_button.pack(side="top", fill="x", pady=(0, 4))

        close_tab_button = ttkb.Button(button_frame, text="✕", width=2, command=self.app.close_current_tab, bootstyle="danger-outline")
        close_tab_button.pack(side="top", fill="x")

        ttk.Separator(button_frame, orient="horizontal").pack(side="top", fill="x", pady=10)
        help_button = ttkb.Button(button_frame, text="?", width=2, command=self.app.show_filter_help, bootstyle="info-outline")
        help_button.pack(side="top", fill="x")

    def create_tab_ui(self, parent_tab_frame: ttkb.Frame, tab_data: Dict[str, Any]) -> None:
        """Creates the UI for a single tab's content area."""
        main_container = ttkb.Frame(parent_tab_frame, padding=(5, 5))
        main_container.pack(fill="both", expand=True)

        options_container = ttkb.LabelFrame(main_container, text="Directory & Options")
        options_container.pack(fill="x", pady=(0, 10))
        self.create_path_selection(options_container, tab_data)
        self.create_options_section(options_container)

        self._create_filter_settings(main_container, tab_data)

        tree_container = ttkb.LabelFrame(main_container, text="Project Structure")
        tree_container.pack(fill="both", expand=True, pady=(10,0))
        self.create_tree_view(tree_container, tab_data)

    def _create_filter_settings(self, parent: ttkb.Frame, tab_data: Dict[str, Any]) -> None:
        """Creates the UI for per-tab include/exclude filter patterns."""
        filter_container = ttkb.LabelFrame(parent, text="Per-Tab Filter Patterns")
        filter_container.pack(fill="x")

        text_area_frame = ttkb.Frame(filter_container)
        text_area_frame.pack(fill="both", expand=True, padx=5, pady=5)
        text_area_frame.grid_columnconfigure(0, weight=1)
        text_area_frame.grid_columnconfigure(1, weight=1)

        exclude_frame = ttkb.Frame(text_area_frame)
        exclude_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 2))
        ttkb.Label(exclude_frame, text="Exclude Patterns").pack(anchor="w", pady=(0, 5))
        exclude_text = ScrolledText(exclude_frame, height=4, font=TERMINAL_FONT, autohide=True, bootstyle="info")
        exclude_text.pack(fill="both", expand=True)
        tab_data["exclude_patterns_text"] = exclude_text

        include_frame = ttkb.Frame(text_area_frame)
        include_frame.grid(row=0, column=1, sticky="nsew", padx=(2, 0))
        ttkb.Label(include_frame, text="Include Patterns (Overrides Exclude)").pack(anchor="w", pady=(0, 5))
        include_text = ScrolledText(include_frame, height=4, font=TERMINAL_FONT, autohide=True, bootstyle="info")
        include_text.pack(fill="both", expand=True)
        tab_data["include_patterns_text"] = include_text

    def create_path_selection(self, parent: ttkb.Frame, tab_data: Dict[str, Any]) -> None:
        """Creates the source directory and output file selection widgets."""
        path_frame = ttkb.Frame(parent, padding=5)
        path_frame.pack(fill='x')
        path_frame.grid_columnconfigure(1, weight=1)

        ttkb.Label(path_frame, text="Source:").grid(row=0, column=0, sticky="w", padx=(0,10))
        source_entry = ttkb.Entry(path_frame, textvariable=tab_data["source_path"])
        source_entry.grid(row=0, column=1, sticky="ew")
        ttkb.Button(path_frame, text="Browse", command=self.app.browse_source, bootstyle="info-outline").grid(row=0, column=2, padx=(10,0))

        ttkb.Label(path_frame, text="Output:").grid(row=1, column=0, sticky="w", padx=(0,10), pady=(5,0))
        output_entry = ttkb.Entry(path_frame, textvariable=tab_data["output_path"])
        output_entry.grid(row=1, column=1, sticky="ew", pady=(5,0))
        ttkb.Button(path_frame, text="Save As", command=self.app.browse_output, bootstyle="info-outline").grid(row=1, column=2, padx=(10,0), pady=(5,0))

    def create_options_section(self, parent: ttkb.Frame) -> None:
        """Creates the selection mode and output options widgets."""
        options_frame = ttkb.Frame(parent, padding=5)
        options_frame.pack(fill="x", expand=True)

        mode_frame = ttkb.Frame(options_frame)
        mode_frame.pack(side="left", padx=(0, 30))
        ttkb.Label(mode_frame, text="Selection Mode:", font=TERMINAL_FONT_BOLD).pack(anchor="w")
        radio_frame = ttkb.Frame(mode_frame)
        radio_frame.pack(fill="x", pady=(5, 0))
        ttkb.Radiobutton(radio_frame, text="Include checked", variable=self.app.include_mode, value=True, bootstyle="info").pack(side="left", padx=(0, 10))
        ttkb.Radiobutton(radio_frame, text="Exclude checked", variable=self.app.include_mode, value=False, bootstyle="info").pack(side="left")

        output_options_frame = ttkb.Frame(options_frame)
        output_options_frame.pack(side="left")
        ttkb.Label(output_options_frame, text="Output Options:", font=TERMINAL_FONT_BOLD).pack(anchor="w")
        content_frame = ttkb.Frame(output_options_frame)
        content_frame.pack(fill="x", pady=(5, 0))
        ttkb.Checkbutton(content_frame, text="Filenames only", variable=self.app.filenames_only, bootstyle="info-round-toggle").pack(side="left", anchor="w", padx=(0, 15))
        ttkb.Checkbutton(content_frame, text="Show excluded in structure", variable=self.app.show_excluded_in_structure, bootstyle="info-round-toggle").pack(side="left", anchor="w")

    def create_tree_view(self, parent: ttkb.Frame, tab_data: Dict[str, Any]) -> None:
        """Creates the scrollable tree view."""
        tree_container = ttkb.Frame(parent)
        tree_container.pack(fill="both", expand=True)
        canvas = tk.Canvas(tree_container, highlightthickness=0, bg=self.app.root.style.colors.bg)
        tab_data["canvas"] = canvas
        scrollbar = ttkb.Scrollbar(tree_container, orient="vertical", command=canvas.yview, bootstyle="info-round")
        scrollable_frame = ttkb.Frame(canvas, style="TFrame")
        tab_data["scrollable_frame"] = scrollable_frame
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mouse_wheel(event):
            if event.num == 5 or (hasattr(event, "delta") and event.delta < 0):
                canvas.yview_scroll(1, "units")
            elif event.num == 4 or (hasattr(event, "delta") and event.delta > 0):
                canvas.yview_scroll(-1, "units")

        def _bind_children(widget: tk.Widget, handler: Callable):
            widget.bind("<MouseWheel>", handler)
            widget.bind("<Button-4>", handler)
            widget.bind("<Button-5>", handler)
            for child in widget.winfo_children():
                _bind_children(child, handler)

        tab_data["bind_scroll_handler"] = lambda w: _bind_children(w, _on_mouse_wheel)
        tab_data["bind_scroll_handler"](scrollable_frame)
        canvas.bind("<MouseWheel>", _on_mouse_wheel)
        canvas.bind("<Button-4>", _on_mouse_wheel)
        canvas.bind("<Button-5>", _on_mouse_wheel)

        self._create_tree_control_buttons(parent, tab_data)

    def _create_tree_control_buttons(self, parent: ttkb.Frame, tab_data: Dict[str, Any]) -> None:
        """Creates the 'Select All', 'Deselect All', and 'Refresh' buttons."""
        tree_controls = ttkb.Frame(parent)
        tree_controls.pack(fill="x", pady=(10, 0))
        ttkb.Button(tree_controls, text="Select All", command=lambda: tab_data["tree_view_manager"].select_all(), bootstyle="info-outline").pack(side="left", padx=(0, 10))
        ttkb.Button(tree_controls, text="Deselect All", command=lambda: tab_data["tree_view_manager"].deselect_all(), bootstyle="info-outline").pack(side="left", padx=(0, 10))
        ttkb.Button(tree_controls, text="Refresh", command=lambda: tab_data["tree_view_manager"].refresh_tree(), bootstyle="info-outline").pack(side="left")

    def create_control_buttons(self, parent: ttkb.Frame) -> None:
        """Creates the main 'Extract Code' button, progress bar, and status label."""
        parent.grid_columnconfigure(1, weight=1)
        self._create_left_controls(parent)
        self._create_center_controls(parent)

    def _create_left_controls(self, parent: ttkb.Frame) -> None:
        """Creates the 'Extract Code' and 'Cancel' buttons."""
        left_controls = ttkb.Frame(parent)
        left_controls.grid(row=0, column=0, sticky="w")
        self.app.extract_btn = ttkb.Button(left_controls, text="Extract Code", command=self.app.file_processor.process_files, bootstyle="success")
        self.app.extract_btn.pack(side="left", padx=(0, 10))
        self.app.cancel_btn = ttkb.Button(left_controls, text="Cancel", command=self.app.file_processor.cancel_processing, bootstyle="danger")
        self.app.cancel_btn.pack_forget()

    def _create_center_controls(self, parent: ttkb.Frame) -> None:
        """Creates the progress bar and status label."""
        center_controls = ttkb.Frame(parent)
        center_controls.grid(row=0, column=1, sticky="ew", padx=20)
        self.app.progress = ttkb.Progressbar(center_controls, length=300, mode="determinate", bootstyle="success-striped")
        self.app.progress.pack(side="left", padx=(0, 15), fill="x", expand=True)
        self.app.status_label = ttkb.Label(center_controls, text="Ready")
        self.app.status_label.pack(side="left")
