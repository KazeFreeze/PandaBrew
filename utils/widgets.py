from textual.widgets import DirectoryTree
from textual.widgets._tree import TreeNode, Tree
from rich.text import Text


class CheckboxDirectoryTree(DirectoryTree):
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

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Called when a node is selected in the tree."""
        if event.node.data is None:
            return
        path_str = str(event.node.data.path)
        if path_str in self.selected_paths:
            self.selected_paths.remove(path_str)
        else:
            self.selected_paths.add(path_str)
        self.refresh()
