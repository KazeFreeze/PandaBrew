import os
from pathlib import Path
from typing import Set

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Button,
    Checkbox,
    Footer,
    Header,
    Input,
    Label,
    RadioButton,
    RadioSet,
    Static,
)

from app.config_manager import ConfigManager
from app.threaded_file_processor import ThreadedFileProcessor
from utils.widgets import CheckboxDirectoryTree


class PandaBrewTUI(App):
    """A Textual TUI for the PandaBrew project extractor."""

    CSS_PATH = "utils/tui.css"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = ConfigManager()
        self.source_path = self.config.get("source_directory", str(Path.home()))
        self.threaded_processor = None

    def on_unmount(self) -> None:
        """Called when the app is unmounted."""
        self.config.save_config()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Called when an input value changes."""
        if event.input.id == "source-directory-input":
            self.source_path = event.value
            self.config.set("source_directory", event.value)
        elif event.input.id == "include-patterns-input":
            self.config.set("include_patterns", event.value)
        elif event.input.id == "exclude-patterns-input":
            self.config.set("exclude_patterns", event.value)

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Called when a radio button changes."""
        self.config.set("include_mode", event.radio_set.pressed_button.value)

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Called when a checkbox changes."""
        if event.checkbox.id == "filenames-only-checkbox":
            self.config.set("filenames_only", event.value)
        elif event.checkbox.id == "show-excluded-checkbox":
            self.config.set("show_excluded_in_structure", event.value)

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(name="PandaBrew")
        with Horizontal(id="main-container"):
            with Vertical(id="left-pane"):
                yield Label("Source Directory:")
                yield Input(
                    value=self.source_path,
                    id="source-directory-input",
                )
                yield Button("Browse", id="browse-button")
                with VerticalScroll(id="directory-tree-container"):
                    yield CheckboxDirectoryTree(self.source_path, id="directory-tree")
            with Vertical(id="right-pane"):
                with RadioSet(id="mode-selection"):
                    yield RadioButton("Include checked items", value=True, id="include-mode")
                    yield RadioButton("Exclude checked items", value=False, id="exclude-mode")
                yield Label("Include Patterns (comma-separated):")
                yield Input(id="include-patterns-input", placeholder="e.g., *.py, *.txt")
                yield Label("Exclude Patterns (comma-separated):")
                yield Input(id="exclude-patterns-input", placeholder="e.g., *.log, .git*")
                yield Checkbox("Filenames only", id="filenames-only-checkbox")
                yield Checkbox("Show excluded in structure", id="show-excluded-checkbox")
                yield Button("Generate Report", variant="primary", id="generate-button")
                yield Static(id="status-label")

        yield Footer()

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        # Load last used settings
        self.query_one("#include-mode").value = self.config.get("include_mode", True)
        self.query_one("#exclude-mode").value = not self.config.get(
            "include_mode", True
        )
        self.query_one("#include-patterns-input").value = self.config.get(
            "include_patterns", ""
        )
        self.query_one("#exclude-patterns-input").value = self.config.get(
            "exclude_patterns", ""
        )
        self.query_one("#filenames-only-checkbox").value = self.config.get(
            "filenames_only", False
        )
        self.query_one("#show-excluded-checkbox").value = self.config.get(
            "show_excluded_in_structure", False
        )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "generate-button":
            self.run_report_generation()
        elif event.button.id == "browse-button":
            self.open_file_dialog()

    def open_file_dialog(self):
        """Opens a file dialog to select a directory."""
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        directory = filedialog.askdirectory(
            initialdir=self.source_path,
            title="Select a directory",
        )
        if directory:
            self.query_one("#source-directory-input").value = directory

    def run_report_generation(self):
        """Gather settings and run the report generation."""
        if self.threaded_processor and self.threaded_processor.is_alive():
            self.threaded_processor.cancel()
            return

        # Gather all the settings from the UI
        source_path = self.query_one("#source-directory-input").value
        include_mode = self.query_one("#include-mode").value
        include_patterns = [
            p.strip()
            for p in self.query_one("#include-patterns-input").value.split(",")
            if p.strip()
        ]
        exclude_patterns = [
            p.strip()
            for p in self.query_one("#exclude-patterns-input").value.split(",")
            if p.strip()
        ]
        filenames_only = self.query_one("#filenames-only-checkbox").value
        show_excluded = self.query_one("#show-excluded-checkbox").value
        selected_paths = self.query_one(CheckboxDirectoryTree).selected_paths
        output_file = (
            f"pandabrew_report_{Path(source_path).name}.md"
        )

        self.threaded_processor = ThreadedFileProcessor(
            output_file,
            source_path,
            include_mode,
            selected_paths,
            include_patterns,
            exclude_patterns,
            filenames_only,
            show_excluded,
        )

        # Start the thread
        self.threaded_processor.start()


if __name__ == "__main__":
    app = PandaBrewTUI()
    app.run()
