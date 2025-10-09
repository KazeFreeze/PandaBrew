from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTreeView,
    QPushButton,
    QHBoxLayout,
)
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt, QDir
from pathlib import Path


class QtTreeViewManager(QWidget):
    def __init__(self, tab_id):
        super().__init__()
        self.tab_id = tab_id
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)
        self.all_expanded = False

        self._create_control_buttons()
        self._create_tree_view()

    def _create_control_buttons(self):
        button_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.select_all)
        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.clicked.connect(self.deselect_all)
        self.toggle_expand_btn = QPushButton("Expand All")
        self.toggle_expand_btn.clicked.connect(self.toggle_expand_all)
        self.refresh_btn = QPushButton("Refresh")
        button_layout.addWidget(self.select_all_btn)
        button_layout.addWidget(self.deselect_all_btn)
        button_layout.addWidget(self.toggle_expand_btn)
        button_layout.addWidget(self.refresh_btn)
        button_layout.addStretch()
        self.layout.addLayout(button_layout)

    def _create_tree_view(self):
        self.tree_view = QTreeView()
        self.model = QStandardItemModel()
        self.tree_view.setModel(self.model)
        self.model.setHorizontalHeaderLabels(["Name"])
        self.layout.addWidget(self.tree_view)

        # Connect signals
        self.model.itemChanged.connect(self.on_item_changed)
        self.tree_view.expanded.connect(self.on_expanded)

    def on_expanded(self, index):
        item = self.model.itemFromIndex(index)
        if item.hasChildren() and item.child(0).text() == "Loading...":
            self.model.removeRow(0, index)
            path = Path(item.data(Qt.UserRole))
            self.populate_directory(item, path)

    def on_item_changed(self, item):
        """Handles checkbox propagation for parent and child items."""
        if not item.isCheckable():
            return

        self.model.blockSignals(True)
        state = item.checkState()
        self._update_children_state(item, state)
        self._update_parent_state(item)
        self.model.blockSignals(False)

    def _update_children_state(self, parent_item, state):
        """Recursively sets the check state for all children of an item."""
        if parent_item.hasChildren():
            for row in range(parent_item.rowCount()):
                child = parent_item.child(row)
                if child.isCheckable() and child.checkState() != state:
                    child.setCheckState(state)

    def _update_parent_state(self, item):
        """Recursively updates the check state of parent items."""
        parent = item.parent()
        if not parent or not parent.isCheckable():
            return

        child_count = parent.rowCount()
        if child_count == 0:
            return

        checked_count = 0
        for row in range(child_count):
            if parent.child(row).checkState() == Qt.CheckState.Checked:
                checked_count += 1

        new_state = parent.checkState()
        if checked_count == child_count:
            new_state = Qt.CheckState.Checked
        else:
            new_state = Qt.CheckState.Unchecked

        if parent.checkState() != new_state:
            parent.setCheckState(new_state)

    def populate_directory(self, parent_item, path):
        dir = QDir(str(path))
        for entry in dir.entryInfoList(QDir.Dirs | QDir.Files | QDir.NoDotAndDotDot, QDir.Name | QDir.DirsFirst):
            item = QStandardItem(entry.fileName())
            item.setCheckable(True)
            item.setData(entry.filePath(), Qt.UserRole)
            parent_item.appendRow(item)
            if entry.isDir():
                # Add a dummy item for lazy loading
                dummy_item = QStandardItem("Loading...")
                item.appendRow(dummy_item)

    def load_directory(self, source_path):
        self.model.clear()
        self.model.setHorizontalHeaderLabels(["Name"])
        root_path = Path(source_path)
        if root_path.is_dir():
            root_item = QStandardItem(root_path.name)
            root_item.setCheckable(True)
            root_item.setData(str(root_path), Qt.UserRole)
            self.model.appendRow(root_item)
            self.populate_directory(root_item, root_path)

    def toggle_expand_all(self):
        if self.all_expanded:
            self.tree_view.collapseAll()
            self.all_expanded = False
            self.toggle_expand_btn.setText("Expand All")
        else:
            self.tree_view.expandAll()
            self.all_expanded = True
            self.toggle_expand_btn.setText("Collapse All")

    def get_checked_paths(self):
        """Recursively finds all checked items and returns their paths."""
        checked_paths = set()
        root = self.model.invisibleRootItem()
        self._find_checked_recursive(root, checked_paths)
        return checked_paths

    def _find_checked_recursive(self, parent_item, checked_paths):
        """Helper method to traverse the model and find checked items."""
        for row in range(parent_item.rowCount()):
            item = parent_item.child(row)
            if item and item.isCheckable() and item.checkState() == Qt.CheckState.Checked:
                path = item.data(Qt.UserRole)
                if path:
                    checked_paths.add(path)
            if item and item.hasChildren():
                self._find_checked_recursive(item, checked_paths)

    def select_all(self):
        """Sets all items in the tree to be checked."""
        self._set_all_items_checked(True)

    def deselect_all(self):
        """Sets all items in the tree to be unchecked."""
        self._set_all_items_checked(False)

    def _set_all_items_checked(self, checked):
        """Recursively sets the checked state for all items."""
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        root = self.model.invisibleRootItem()
        for row in range(root.rowCount()):
            item = root.child(row)
            self._set_item_checked_recursive(item, state)

    def _set_item_checked_recursive(self, parent_item, state):
        """Helper method to set the checked state for an item and its children."""
        if parent_item and parent_item.isCheckable():
            parent_item.setCheckState(state)
        if parent_item and parent_item.hasChildren():
            for row in range(parent_item.rowCount()):
                item = parent_item.child(row)
                self._set_item_checked_recursive(item, state)
