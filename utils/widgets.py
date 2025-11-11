from textual.widgets import DirectoryTree
from textual.widgets._tree import TreeNode, Tree
from rich.text import Text
from textual.binding import Binding


class CheckboxDirectoryTree(DirectoryTree):
    BINDINGS = [
        Binding("space", "toggle_selection", "Toggle Selection"),
    ]

    def __init__(self, path, id=None):
        super().__init__(path, id=id)
        self.selected_paths = set()

    def _render_node(self, node: TreeNode) -> Text:
        """Renders a node in the directory tree."""
        if node.data is None:
            return Text(f"[ ] {node.label}")
        path_str = str(node.data.path)
        is_selected = path_str in self.selected_paths
        checkbox = "[x]" if is_selected else "[ ]"
        return Text(f"{checkbox} {node.label}")

    def action_toggle_selection(self) -> None:
        """Toggles the selection of the currently highlighted node."""
        if self.cursor_node and self.cursor_node.data:
            path_str = str(self.cursor_node.data.path)
            if path_str in self.selected_paths:
                self.selected_paths.remove(path_str)
            else:
                self.selected_paths.add(path_str)
            self.refresh()

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Called when a node is selected in the tree."""
        self.action_toggle_selection()
