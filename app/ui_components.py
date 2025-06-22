import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttkb
from pathlib import Path


class UIComponents:
    """
    Manages the creation and layout of all the UI components.
    The structure is now split between a main layout and the UI for each tab.
    """

    def __init__(self, app_instance):
        """
        Initializes the UIComponents class.
        """
        self.app = app_instance

    def create_main_layout(self):
        """
        Creates the main layout of the application, which contains the notebook
        and the final control/status bar section.
        """
        control_container = ttkb.Frame(self.app.root, padding=(10, 10))
        control_container.pack(fill="x", side="bottom")

        self.create_control_buttons(control_container)

    def create_tab_ui(self, parent_tab_frame, tab_data):
        """
        Creates the UI for a single tab, including path selection and the tree view.
        """
        main_container = ttkb.Frame(parent_tab_frame, padding=(5, 5))
        main_container.pack(fill="both", expand=True)

        header_frame = ttkb.LabelFrame(
            main_container, text="Directory & Options", padding=15
        )
        header_frame.pack(fill="x", pady=(0, 10))

        self.create_path_selection(header_frame, tab_data)
        self.create_options_section(header_frame)

        tree_frame = ttkb.LabelFrame(
            main_container, text="Project Structure", padding=15
        )
        tree_frame.pack(fill="both", expand=True)
        self.create_tree_view(tree_frame, tab_data)

    def create_path_selection(self, parent, tab_data):
        """
        Creates the UI elements for selecting the source directory for a specific tab.
        """
        source_section = ttkb.Frame(parent)
        source_section.pack(fill="x", pady=(0, 10))

        ttkb.Label(
            source_section, text="Source Directory:", font=("Segoe UI", 9, "bold")
        ).pack(anchor="w")

        source_input_frame = ttkb.Frame(source_section)
        source_input_frame.pack(fill="x", pady=(5, 0))

        source_entry = ttkb.Entry(
            source_input_frame,
            textvariable=tab_data["source_path"],
            font=("Segoe UI", 9),
        )
        source_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ttkb.Button(
            source_input_frame, text="Browse", command=self.app.browse_source
        ).pack(side="right")

    def create_options_section(self, parent):
        """
        Creates the global options section (mode, output content).
        """
        options_frame = ttkb.Frame(parent)
        options_frame.pack(fill="x", expand=True, pady=(10, 0))
        options_frame.grid_columnconfigure(2, weight=1)

        mode_frame = ttkb.Frame(options_frame)
        mode_frame.grid(row=0, column=0, padx=(0, 30), sticky="w")
        ttkb.Label(
            mode_frame, text="Selection Mode:", font=("Segoe UI", 9, "bold")
        ).pack(anchor="w")
        radio_frame = ttkb.Frame(mode_frame)
        radio_frame.pack(fill="x", pady=(5, 0))
        ttkb.Radiobutton(
            radio_frame,
            text="Include checked",
            variable=self.app.include_mode,
            value=True,
        ).pack(side="left", padx=(0, 10))
        ttkb.Radiobutton(
            radio_frame,
            text="Exclude checked",
            variable=self.app.include_mode,
            value=False,
        ).pack(side="left")

        output_options_frame = ttkb.Frame(options_frame)
        output_options_frame.grid(row=0, column=1, padx=(0, 30), sticky="w")
        ttkb.Label(
            output_options_frame, text="Output Content:", font=("Segoe UI", 9, "bold")
        ).pack(anchor="w")
        content_frame = ttkb.Frame(output_options_frame)
        content_frame.pack(fill="x", pady=(5, 0))
        ttkb.Checkbutton(
            content_frame, text="Filenames only", variable=self.app.filenames_only
        ).pack(anchor="w")

        output_section = ttkb.Frame(options_frame)
        output_section.grid(row=0, column=2, sticky="ew")
        ttkb.Label(
            output_section, text="Output File:", font=("Segoe UI", 9, "bold")
        ).pack(anchor="w")
        output_input_frame = ttkb.Frame(output_section)
        output_input_frame.pack(fill="x", expand=True, pady=(5, 0))
        output_entry = ttkb.Entry(
            output_input_frame, textvariable=self.app.output_path, font=("Segoe UI", 9)
        )
        output_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ttkb.Button(
            output_input_frame, text="Save As", command=self.app.browse_output
        ).pack(side="right")

    def create_tree_view(self, parent, tab_data):
        """
        Creates the tree view area for a specific tab.
        """
        tree_container = ttkb.Frame(parent)
        tree_container.pack(fill="both", expand=True)

        canvas = tk.Canvas(
            tree_container, highlightthickness=0, bg=self.app.root.style.colors.bg
        )
        tab_data["canvas"] = canvas

        scrollbar = ttkb.Scrollbar(
            tree_container, orient="vertical", command=canvas.yview
        )
        scrollable_frame = ttkb.Frame(canvas)
        tab_data["scrollable_frame"] = scrollable_frame

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # NOTE: The mousewheel binding is now handled globally in app.py for robustness.

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
            bootstyle="info-outline",
        ).pack(side="left")

    def create_control_buttons(self, parent):
        """
        Creates the main control buttons (Extract) and the progress bar.
        """
        parent.grid_columnconfigure(1, weight=1)

        left_controls = ttkb.Frame(parent)
        left_controls.grid(row=0, column=0, sticky="w")
        extract_btn = ttkb.Button(
            left_controls,
            text="Extract Code",
            command=self.app.file_processor.process_files,
            bootstyle="success",
        )
        extract_btn.pack(side="left", padx=(0, 10))

        center_controls = ttkb.Frame(parent)
        center_controls.grid(row=0, column=1, sticky="ew", padx=20)
        self.app.progress = ttkb.Progressbar(
            center_controls, length=300, mode="determinate"
        )
        self.app.progress.pack(side="left", padx=(0, 15), fill="x", expand=True)
        self.app.status_label = ttkb.Label(
            center_controls, text="Ready", font=("Segoe UI", 9)
        )
        self.app.status_label.pack(side="left")
