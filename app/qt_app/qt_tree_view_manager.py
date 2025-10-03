from PySide6.QtCore import Qt, QDir
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon
from PySide6.QtWidgets import QTreeView, QHeaderView
from pathlib import Path
from typing import Set, Dict

from utils.helpers import format_file_size

class QtTreeViewManager:
    """
    Manages the QTreeView, including populating it with a file system model,
    handling check state logic, and providing selection functions.
    """
    def __init__(self, tree_view: QTreeView):
        self.tree_view = tree_view
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Name', 'Size'])
        self.tree_view.setModel(self.model)
        header = self.tree_view.header()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)

        self.checked_paths: Set[str] = set()
        self.path_to_item_map: Dict[str, QStandardItem] = {}

        self._is_updating_checks = False

        self.model.itemChanged.connect(self.on_item_changed)
        self.tree_view.expanded.connect(self.on_item_expanded)

    def refresh_tree(self, source_path: str):
        """Clears the current tree and populates it from the new source path."""
        self.model.clear()
        self.path_to_item_map.clear()
        self.model.setHorizontalHeaderLabels(['Name', 'Size'])

        root_path = Path(source_path)
        if root_path.exists() and root_path.is_dir():
            self._add_item(self.model.invisibleRootItem(), root_path)
            root_item = self.model.item(0)
            if root_item:
                self.tree_view.expand(root_item.index())

    def _add_item(self, parent_item: QStandardItem, path: Path):
        """Adds a single item to the tree and sets up its properties."""
        path_str = str(path)

        item = QStandardItem(path.name)
        item.setCheckable(True)
        item.setEditable(False)
        item.setData(path_str, Qt.UserRole)

        if path_str in self.checked_paths:
            item.setCheckState(Qt.Checked)

        size_str = format_file_size(path.stat().st_size) if path.is_file() else ""
        size_item = QStandardItem(size_str)
        size_item.setEditable(False)
        size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

        parent_item.appendRow([item, size_item])
        self.path_to_item_map[path_str] = item

        if path.is_dir():
            item.setIcon(QIcon.fromTheme("folder", QIcon(":/qt-project.org/styles/commonstyle/images/diropen-128.png")))
            if any(path.iterdir()):
                dummy_item = QStandardItem()
                item.appendRow(dummy_item)
        else:
            item.setIcon(QIcon.fromTheme("text-x-generic", QIcon(":/qt-project.org/styles/commonstyle/images/file-128.png")))

    def on_item_expanded(self, index):
        """Lazy-loads the children of a directory when it's expanded."""
        item = self.model.itemFromIndex(index)
        if not item: return

        if item.rowCount() > 0 and not item.child(0).hasChildren() and not item.child(0).text():
            item.removeRows(0, item.rowCount())

            path = Path(item.data(Qt.UserRole))
            try:
                for child_path in sorted(list(path.iterdir()), key=lambda p: (p.is_file(), p.name.lower())):
                    self._add_item(item, child_path)
            except (IOError, PermissionError) as e:
                print(f"Error expanding {path}: {e}")

    def on_item_changed(self, item: QStandardItem):
        """Handles the logic when a checkbox is clicked."""
        if self._is_updating_checks:
            return

        self._is_updating_checks = True
        try:
            path_str = item.data(Qt.UserRole)
            is_checked = item.checkState() == Qt.Checked

            if path_str in self.path_to_item_map:
                self._update_descendants(self.path_to_item_map[path_str], is_checked)

            self._update_parents(item)
        finally:
            self._is_updating_checks = False

    def _update_descendants(self, parent_item: QStandardItem, is_checked: bool):
        """Recursively update the check state of all descendant items."""
        check_state = Qt.Checked if is_checked else Qt.Unchecked
        if parent_item.checkState() == check_state:
            return

        parent_item.setCheckState(check_state)
        path_str = parent_item.data(Qt.UserRole)
        if is_checked:
            self.checked_paths.add(path_str)
        else:
            self.checked_paths.discard(path_str)

        for row in range(parent_item.rowCount()):
            child_item = parent_item.child(row, 0)
            if child_item:
                self._update_descendants(child_item, is_checked)

    def _update_parents(self, item: QStandardItem):
        """Recursively update the check state of parent items."""
        parent = item.parent()
        while parent:
            if parent.checkState() == Qt.PartiallyChecked:
                parent.setCheckState(Qt.Checked) # Or some other logic

            all_children_checked = True
            for row in range(parent.rowCount()):
                child = parent.child(row, 0)
                if child and child.checkState() != Qt.Checked:
                    all_children_checked = False
                    break

            check_state = Qt.Checked if all_children_checked else Qt.Unchecked
            if parent.checkState() != check_state:
                parent.setCheckState(check_state)

            path_str = parent.data(Qt.UserRole)
            if all_children_checked:
                self.checked_paths.add(path_str)
            else:
                self.checked_paths.discard(path_str)

            parent = parent.parent()

    def select_all(self):
        """Selects all items in the tree."""
        self._is_updating_checks = True
        root = self.model.invisibleRootItem()
        for row in range(root.rowCount()):
            item = root.child(row, 0)
            if item:
                self._update_descendants(item, True)
        self._is_updating_checks = False

    def deselect_all(self):
        """Deselects all items in the tree."""
        self._is_updating_checks = True
        root = self.model.invisibleRootItem()
        for row in range(root.rowCount()):
            item = root.child(row, 0)
            if item:
                self._update_descendants(item, False)
        self._is_updating_checks = False