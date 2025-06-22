import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttkb
from pathlib import Path
from typing import Dict, Any

# Define a consistent font for the terminal theme
TERMINAL_FONT = ("Cascadia Code", 9)
TERMINAL_FONT_BOLD = ("Cascadia Code", 9, "bold")
TREE_FONT = ("Consolas", 10)


class UIComponents:
    """
    Manages the creation and layout of all the UI components.
    This version uses a simplified and robust tab management approach
    and is styled for a dark, terminal-like theme.
    """

    def __init__(self, app_instance):
        self.app = app_instance
        self.notebook = None
        self._configure_styles()

    def _configure_styles(self) -> None:
        """Configures custom ttk styles for the terminal theme."""
        style = self.app.style

        # General widget styling
        style.configure(".", font=TERMINAL_FONT)
        style.configure("TLabel", font=TERMINAL_FONT)
        style.configure("TButton", font=TERMINAL_FONT_BOLD)
        style.configure("Toolbutton", font=TERMINAL_FONT)
        style.configure("TCheckbutton", font=TERMINAL_FONT)
        style.configure("TRadiobutton", font=TERMINAL_FONT)
        style.configure("TEntry", font=TERMINAL_FONT)

        # LabelFrame styling using a brighter 'info' color for the title
        style.configure("TLabelframe", padding=15)
        style.configure(
            "TLabelframe.Label",
            font=TERMINAL_FONT_BOLD,
            foreground=style.colors.get("info"),
        )

        # Notebook styling for a more integrated look
        style.configure("TNotebook.Tab", font=TERMINAL_FONT_BOLD, padding=[10, 5])
        style.map(
            "TNotebook.Tab",
            foreground=[
                ("selected", style.colors.get("info")),
                ("!selected", style.colors.get("fg")),
            ],
            background=[
                ("selected", style.colors.get("bg")),
                ("!selected", style.colors.get("light")),
            ],
        )

    def create_main_layout(self) -> None:
        """
        Creates the main layout of the application, including the tab container
        and the final control/status bar section.
        """
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
        """Creates the '+' and 'x' buttons for tab management."""
        button_frame = ttkb.Frame(parent)
        button_frame.pack(side="left", anchor="n", fill="y", padx=(2, 0), pady=2)

        add_tab_button = ttkb.Button(
            button_frame,
            text="+",
            width=2,
            command=self.app.add_new_tab,
            bootstyle="success-outline",
        )
        add_tab_button.pack(side="top", fill="x")

        close_tab_button = ttkb.Button(
            button_frame,
            text="✕",
            width=2,
            command=self.app.close_current_tab,
            bootstyle="danger-outline",
        )
        close_tab_button.pack(side="top", fill="x", pady=(4, 0))

    def create_tab_ui(
        self, parent_tab_frame: ttkb.Frame, tab_data: Dict[str, Any]
    ) -> None:
        """
        Creates the UI for a single tab's content area.
        """
        main_container = ttkb.Frame(parent_tab_frame, padding=(5, 5))
        main_container.pack(fill="both", expand=True)

        options_container = ttkb.LabelFrame(main_container, text="Directory & Options")
        options_container.pack(fill="x", pady=(0, 10))

        self.create_path_selection(options_container, tab_data)
        self.create_options_section(options_container, tab_data)

        tree_container = ttkb.LabelFrame(main_container, text="Project Structure")
        tree_container.pack(fill="both", expand=True)
        self.create_tree_view(tree_container, tab_data)

    def create_path_selection(
        self, parent: ttkb.Frame, tab_data: Dict[str, Any]
    ) -> None:
        """Creates the source directory selection widgets."""
        source_section = ttkb.Frame(parent)
        source_section.pack(fill="x", pady=(0, 10))
        ttkb.Label(
            source_section, text="Source Directory:", font=TERMINAL_FONT_BOLD
        ).pack(anchor="w")
        source_input_frame = ttkb.Frame(source_section)
        source_input_frame.pack(fill="x", pady=(5, 0))
        source_entry = ttkb.Entry(
            source_input_frame,
            textvariable=tab_data["source_path"],
        )
        source_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ttkb.Button(
            source_input_frame,
            text="Browse",
            command=self.app.browse_source,
            bootstyle="info-outline",
        ).pack(side="right")

    def create_options_section(
        self, parent: ttkb.Frame, tab_data: Dict[str, Any]
    ) -> None:
        """Creates the selection mode and output options widgets."""
        options_frame = ttkb.Frame(parent)
        options_frame.pack(fill="x", expand=True, pady=(10, 0))
        options_frame.grid_columnconfigure(2, weight=1)
        self._create_selection_mode_widgets(options_frame)
        self._create_output_content_widgets(options_frame)
        self._create_output_file_widgets(options_frame, tab_data)

    def _create_selection_mode_widgets(self, parent: ttkb.Frame) -> None:
        """Creates the 'Include/Exclude' radio buttons."""
        mode_frame = ttkb.Frame(parent)
        mode_frame.grid(row=0, column=0, padx=(0, 30), sticky="w")
        ttkb.Label(mode_frame, text="Selection Mode:", font=TERMINAL_FONT_BOLD).pack(
            anchor="w"
        )
        radio_frame = ttkb.Frame(mode_frame)
        radio_frame.pack(fill="x", pady=(5, 0))
        ttkb.Radiobutton(
            radio_frame,
            text="Include checked",
            variable=self.app.include_mode,
            value=True,
            bootstyle="info",
        ).pack(side="left", padx=(0, 10))
        ttkb.Radiobutton(
            radio_frame,
            text="Exclude checked",
            variable=self.app.include_mode,
            value=False,
            bootstyle="info",
        ).pack(side="left")

    def _create_output_content_widgets(self, parent: ttkb.Frame) -> None:
        """Creates the 'Filenames only' checkbox."""
        output_options_frame = ttkb.Frame(parent)
        output_options_frame.grid(row=0, column=1, padx=(0, 30), sticky="w")
        ttkb.Label(
            output_options_frame, text="Output Content:", font=TERMINAL_FONT_BOLD
        ).pack(anchor="w")
        content_frame = ttkb.Frame(output_options_frame)
        content_frame.pack(fill="x", pady=(5, 0))
        ttkb.Checkbutton(
            content_frame,
            text="Filenames only",
            variable=self.app.filenames_only,
            bootstyle="info-round-toggle",
        ).pack(anchor="w")

    def _create_output_file_widgets(
        self, parent: ttkb.Frame, tab_data: Dict[str, Any]
    ) -> None:
        """Creates the output file selection widgets."""
        output_section = ttkb.Frame(parent)
        output_section.grid(row=0, column=2, sticky="ew")
        ttkb.Label(output_section, text="Output File:", font=TERMINAL_FONT_BOLD).pack(
            anchor="w"
        )
        output_input_frame = ttkb.Frame(output_section)
        output_input_frame.pack(fill="x", expand=True, pady=(5, 0))
        output_entry = ttkb.Entry(
            output_input_frame, textvariable=tab_data["output_path"]
        )
        output_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ttkb.Button(
            output_input_frame,
            text="Save As",
            command=self.app.browse_output,
            bootstyle="info-outline",
        ).pack(side="right")

    def create_tree_view(self, parent: ttkb.Frame, tab_data: Dict[str, Any]) -> None:
        """Creates the scrollable tree view."""
        tree_container = ttkb.Frame(parent)
        tree_container.pack(fill="both", expand=True)

        # Use a transparent background for the canvas to let the mica show through
        canvas = tk.Canvas(
            tree_container, highlightthickness=0, bg=self.app.root.style.colors.bg
        )
        tab_data["canvas"] = canvas

        scrollbar = ttkb.Scrollbar(
            tree_container,
            orient="vertical",
            command=canvas.yview,
            bootstyle="info-round",
        )
        scrollable_frame = ttkb.Frame(canvas, style="TFrame")
        tab_data["scrollable_frame"] = scrollable_frame

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._create_tree_control_buttons(parent, tab_data)

    def _create_tree_control_buttons(
        self, parent: ttkb.Frame, tab_data: Dict[str, Any]
    ) -> None:
        """Creates the 'Select All', 'Deselect All', and 'Refresh' buttons."""
        tree_controls = ttkb.Frame(parent)
        tree_controls.pack(fill="x", pady=(10, 0))
        ttkb.Button(
            tree_controls,
            text="Select All",
            command=lambda: tab_data["tree_view_manager"].select_all(),
            bootstyle="info-outline",
        ).pack(side="left", padx=(0, 10))
        ttkb.Button(
            tree_controls,
            text="Deselect All",
            command=lambda: tab_data["tree_view_manager"].deselect_all(),
            bootstyle="info-outline",
        ).pack(side="left", padx=(0, 10))
        ttkb.Button(
            tree_controls,
            text="Refresh",
            command=lambda: tab_data["tree_view_manager"].refresh_tree(),
            bootstyle="info-outline",  # Changed to info-outline for consistency
        ).pack(side="left")

    def create_control_buttons(self, parent: ttkb.Frame) -> None:
        """Creates the main 'Extract Code' button, progress bar, and status label."""
        parent.grid_columnconfigure(1, weight=1)
        self._create_left_controls(parent)
        self._create_center_controls(parent)

    def _create_left_controls(self, parent: ttkb.Frame) -> None:
        """Creates the 'Extract Code' and 'Cancel' buttons."""
        left_controls = ttkb.Frame(parent)
        left_controls.grid(row=0, column=0, sticky="w")

        # Assign button to the app instance
        self.app.extract_btn = ttkb.Button(
            left_controls,
            text="Extract Code",
            command=self.app.file_processor.process_files,
            bootstyle="success",
        )
        self.app.extract_btn.pack(side="left", padx=(0, 10))

        # Assign cancel button to the app instance
        self.app.cancel_btn = ttkb.Button(
            left_controls,
            text="Cancel",
            command=self.app.file_processor.cancel_processing,
            bootstyle="danger",
        )
        # The cancel button is hidden by default and managed by the app state
        self.app.cancel_btn.pack_forget()

    def _create_center_controls(self, parent: ttkb.Frame) -> None:
        """Creates the progress bar and status label."""
        center_controls = ttkb.Frame(parent)
        center_controls.grid(row=0, column=1, sticky="ew", padx=20)

        # Assign progress bar and status label to the app instance
        self.app.progress = ttkb.Progressbar(
            center_controls, length=300, mode="determinate", bootstyle="success-striped"
        )
        self.app.progress.pack(side="left", padx=(0, 15), fill="x", expand=True)

        self.app.status_label = ttkb.Label(center_controls, text="Ready")
        self.app.status_label.pack(side="left")
