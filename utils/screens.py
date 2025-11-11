from textual.screen import ModalScreen
from textual.widgets import DirectoryTree, Button
from textual.containers import Vertical


class SelectDirectoryScreen(ModalScreen):
    """A modal screen to select a directory."""

    def compose(self):
        with Vertical(id="select-directory-container"):
            yield DirectoryTree("/", id="select-directory-tree")
            yield Button("Select", variant="primary", id="select-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Called when the select button is pressed."""
        if event.button.id == "select-button":
            tree = self.query_one(DirectoryTree)
            self.dismiss(tree.cursor_node.data.path)
