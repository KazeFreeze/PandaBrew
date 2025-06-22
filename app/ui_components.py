import tkinter as tk
import ttkbootstrap as ttkb


class UIComponents:
    """
    Manages the creation and layout of all the UI components in the main window.
    """

    def __init__(self, app_instance):
        """
        Initializes the UIComponents class.

        Args:
            app_instance: An instance of the main application class.
        """
        self.app = app_instance

    def create_modern_gui(self):
        """
        Creates the main graphical user interface for the application.
        """
        main_container = ttkb.Frame(self.app.root, padding=(20, 20))
        main_container.pack(fill="both", expand=True)

        header_frame = ttkb.LabelFrame(
            main_container,
            text="Project Settings",
            padding=20,
        )
        header_frame.pack(fill="x", pady=(0, 15))

        self.create_path_selection(header_frame)
        self.create_options_section(header_frame)

        tree_frame = ttkb.LabelFrame(
            main_container,
            text="Project Structure",
            padding=15,
        )
        tree_frame.pack(fill="both", expand=True, pady=(0, 15))

        self.create_tree_view(tree_frame)
        self.create_control_buttons(main_container)

    def create_path_selection(self, parent):
        """
        Creates the UI elements for selecting the source and output paths.

        Args:
            parent (tk.Widget): The parent widget for these components.
        """
        source_section = ttkb.Frame(parent)
        source_section.pack(fill="x", pady=(0, 15))

        ttkb.Label(
            source_section, text="Source Directory:", font=("Segoe UI", 9, "bold")
        ).pack(anchor="w")

        source_input_frame = ttkb.Frame(source_section)
        source_input_frame.pack(fill="x", pady=(5, 0))

        source_entry = ttkb.Entry(
            source_input_frame,
            textvariable=self.app.source_path,
            font=("Segoe UI", 9),
            width=80,
        )
        source_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ttkb.Button(
            source_input_frame,
            text="Browse",
            command=self.app.browse_source,
        ).pack(side="right")

        self.create_recent_dropdown(
            source_input_frame,
            source_entry,
            "recent_sources",
            lambda p: (
                self.app.source_path.set(p),
                self.app.tree_view_manager.refresh_tree(),
            ),
        )

        output_section = ttkb.Frame(parent)
        output_section.pack(fill="x", pady=(10, 0))

        ttkb.Label(
            output_section, text="Output File:", font=("Segoe UI", 9, "bold")
        ).pack(anchor="w")

        output_input_frame = ttkb.Frame(output_section)
        output_input_frame.pack(fill="x", pady=(5, 0))

        output_entry = ttkb.Entry(
            output_input_frame,
            textvariable=self.app.output_path,
            font=("Segoe UI", 9),
            width=80,
        )
        output_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ttkb.Button(
            output_input_frame,
            text="Save As",
            command=self.app.browse_output,
        ).pack(side="right")

        self.create_recent_dropdown(
            output_input_frame,
            output_entry,
            "recent_outputs",
            lambda p: self.app.output_path.set(p),
        )

    def create_recent_dropdown(self, parent, entry_widget, config_key, command):
        """
        Creates a dropdown menu for recently used paths.
        """
        if self.app.config.get(config_key):
            dropdown_btn = ttkb.Button(
                parent,
                text="▼",
                width=3,
                command=lambda: self.show_recent_menu(
                    dropdown_btn, config_key, command
                ),
            )
            dropdown_btn.pack(side="right", padx=(5, 0))

    def show_recent_menu(self, button, config_key, command):
        """
        Displays the menu of recent paths.
        """
        menu = tk.Menu(self.app.root, tearoff=0)
        for path in reversed(self.app.config.get(config_key, [])):
            menu.add_command(label=path, command=lambda p=path: command(p))

        x = button.winfo_rootx()
        y = button.winfo_rooty() + button.winfo_height()
        menu.post(x, y)

    def create_options_section(self, parent):
        """
        Creates the options section with include/exclude and other settings.
        """
        options_frame = ttkb.LabelFrame(parent, text="Options", padding=10)
        options_frame.pack(fill="x", pady=(15, 0))

        mode_frame = ttkb.Frame(options_frame)
        mode_frame.pack(fill="x", pady=(0, 10))

        ttkb.Label(
            mode_frame, text="Selection Mode:", font=("Segoe UI", 9, "bold")
        ).pack(anchor="w")

        radio_frame = ttkb.Frame(mode_frame)
        radio_frame.pack(fill="x", pady=(5, 0))

        ttkb.Radiobutton(
            radio_frame,
            text="Include checked items",
            variable=self.app.include_mode,
            value=True,
        ).pack(side="left", padx=(0, 20))
        ttkb.Radiobutton(
            radio_frame,
            text="Exclude checked items",
            variable=self.app.include_mode,
            value=False,
        ).pack(side="left")

        output_options_frame = ttkb.Frame(options_frame)
        output_options_frame.pack(fill="x")

        ttkb.Label(
            output_options_frame, text="Output Content:", font=("Segoe UI", 9, "bold")
        ).pack(anchor="w")

        content_frame = ttkb.Frame(output_options_frame)
        content_frame.pack(fill="x", pady=(5, 0))

        ttkb.Checkbutton(
            content_frame,
            text="Filenames only (no file content)",
            variable=self.app.filenames_only,
        ).pack(anchor="w")

    def create_tree_view(self, parent):
        """
        Creates the tree view area with a scrollable canvas.
        """
        tree_container = ttkb.Frame(parent)
        tree_container.pack(fill="both", expand=True)

        self.app.canvas = tk.Canvas(tree_container, highlightthickness=0)
        self.app.canvas.configure(bg=self.app.root.style.colors.bg)

        scrollbar = ttkb.Scrollbar(
            tree_container, orient="vertical", command=self.app.canvas.yview
        )
        self.app.scrollable_frame = ttkb.Frame(self.app.canvas)

        self.app.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.app.canvas.configure(
                scrollregion=self.app.canvas.bbox("all")
            ),
        )

        self.app.canvas.create_window(
            (0, 0), window=self.app.scrollable_frame, anchor="nw"
        )
        self.app.canvas.configure(yscrollcommand=scrollbar.set)

        self.app.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            self.app.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.app.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        tree_controls = ttkb.Frame(parent)
        tree_controls.pack(fill="x", pady=(10, 0))

        ttkb.Button(
            tree_controls,
            text="Select All",
            command=self.app.tree_view_manager.select_all,
            bootstyle="info-outline",
        ).pack(side="left", padx=(0, 10))
        ttkb.Button(
            tree_controls,
            text="Deselect All",
            command=self.app.tree_view_manager.deselect_all,
            bootstyle="info-outline",
        ).pack(side="left", padx=(0, 10))
        ttkb.Button(
            tree_controls,
            text="Refresh",
            command=self.app.tree_view_manager.refresh_tree,
            bootstyle="info-outline",
        ).pack(side="left")

    def create_control_buttons(self, parent):
        """
        Creates the main control buttons like 'Extract' and the progress bar.
        """
        control_frame = ttkb.Frame(parent)
        control_frame.pack(fill="x")

        left_controls = ttkb.Frame(control_frame)
        left_controls.pack(side="left")

        extract_btn = ttkb.Button(
            left_controls,
            text="Extract Code",
            command=self.app.file_processor.process_files,
            bootstyle="success",
        )
        extract_btn.pack(side="left", padx=(0, 20))

        center_controls = ttkb.Frame(control_frame)
        center_controls.pack(side="left", fill="x", expand=True)

        self.app.progress = ttkb.Progressbar(
            center_controls, length=300, mode="determinate"
        )
        self.app.progress.pack(side="left", padx=(0, 15))

        self.app.status_label = ttkb.Label(
            center_controls, text="Ready", font=("Segoe UI", 9)
        )
        self.app.status_label.pack(side="left")
