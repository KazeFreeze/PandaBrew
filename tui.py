from pathlib import Path
import threading
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import (
    Header,
    Footer,
    Button,
    Checkbox,
    DirectoryTree,
    Input,
    Label,
    ProgressBar,
    RadioButton,
    RadioSet,
)
from textual.widgets.tree import TreeNode
from rich.text import Text

from app.core import generate_report_to_file


class SelectableDirectoryTree(DirectoryTree):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.selected_nodes = set()

    def render_label(self, node: TreeNode, base_style, style):
        label = super().render_label(node, base_style, style)
        if node.data.path in self.selected_nodes:
            label.stylize("reverse")
        return label

    def on_tree_node_selected(self, event: DirectoryTree.FileSelected):
        if event.node.data.path in self.selected_nodes:
            self.selected_nodes.remove(event.node.data.path)
        else:
            self.selected_nodes.add(event.node.data.path)
        self.refresh()


class TUI(App):
    TITLE = "PandaBrew"
    SUB_TITLE = "Selectively extract project source code"

    def compose(self) -> ComposeResult:
        yield Header()
        with Container():
            with Vertical(id="left-pane"):
                yield Label("Source Directory:")
                yield Input(placeholder="/path/to/source", id="source_dir")
                yield Label("Output File:")
                yield Input(placeholder="/path/to/output.txt", id="output_file")
                yield Label("Include Patterns File:")
                yield Input(placeholder="/path/to/include.txt", id="include_file")
                yield Label("Exclude Patterns File:")
                yield Input(placeholder="/path/to/exclude.txt", id="exclude_file")
                with RadioSet(id="mode"):
                    yield RadioButton("Include", value=True, id="include_mode")
                    yield RadioButton("Exclude", id="exclude_mode")
                yield Checkbox("Filenames only", id="filenames_only")
                yield Checkbox("Show excluded", id="show_excluded")
                yield Button("Generate Report", id="generate")
                yield ProgressBar(id="progress", total=100, show_eta=False)
            with Vertical(id="right-pane"):
                yield Label("Navigate with arrows, press Enter to select.")
                yield SelectableDirectoryTree(path=Path.cwd(), id="tree")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#source_dir").focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "source_dir":
            source_path = Path(event.value)
            if source_path.is_dir():
                tree = self.query_one(SelectableDirectoryTree)
                tree.path = source_path
                tree.focus()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "generate":
            self.run_generation()

    def run_generation(self) -> None:
        source_dir = self.query_one("#source_dir").value
        output_file = self.query_one("#output_file").value
        include_file = self.query_one("#include_file").value
        exclude_file = self.query_one("#exclude_file").value
        include_mode = self.query_one("#include_mode").value
        filenames_only = self.query_one("#filenames_only").value
        show_excluded = self.query_one("#show_excluded").value
        tree = self.query_one(SelectableDirectoryTree)
        manual_selections = {str(path) for path in tree.selected_nodes}

        def read_patterns(path: str) -> list[str]:
            if not path:
                return []
            try:
                with open(path, "r") as f:
                    return [
                        line.strip()
                        for line in f
                        if line.strip() and not line.strip().startswith("#")
                    ]
            except FileNotFoundError:
                return []

        include_patterns = read_patterns(include_file)
        exclude_patterns = read_patterns(exclude_file)
        cancel_event = threading.Event()

        def progress_callback(progress: float, status: str) -> None:
            self.call_from_thread(
                self.query_one(ProgressBar).update, progress=progress
            )

        threading.Thread(
            target=generate_report_to_file,
            args=(
                output_file,
                source_dir,
                include_mode,
                manual_selections,
                include_patterns,
                exclude_patterns,
                filenames_only,
                show_excluded,
                cancel_event,
                progress_callback,
            ),
        ).start()


if __name__ == "__main__":
    app = TUI()
    app.run()
