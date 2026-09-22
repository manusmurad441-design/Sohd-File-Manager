"""Sohd File Manager 0.1 desktop application."""

from __future__ import annotations

import html
import os
import shutil
import sys
from pathlib import Path

from PyQt6.QtCore import QDir, QTimer, QUrl, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QDesktopServices, QFileSystemModel, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QSplitter,
    QToolBar,
    QTreeView,
    QVBoxLayout,
    QWidget,
)
from file_core import (
    FileProperties,
    copy_items,
    create_folder,
    delete_items,
    display_size,
    move_items,
    open_path,
    properties,
    rename_path,
    search_files,
    storage_info,
)

APP_NAME = "Sohd File Manager"
APP_VERSION = "0.1.0"


class PropertiesDialog(QDialog):
    def __init__(self, info: FileProperties, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(f"Properties — {info.name}")
        self.resize(620, 360)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.addRow("Name", QLabel(info.name))
        form.addRow("Path", QLabel(str(info.path)))
        form.addRow("Type", QLabel(info.kind))
        form.addRow("Size", QLabel(display_size(info.size)))
        form.addRow("Modified", QLabel(info.modified))
        form.addRow("Permissions", QLabel(info.permissions))
        if info.package_manifest:
            manifest_text = (
                f"{info.package_manifest.get('name', 'Unknown')} "
                f"{info.package_manifest.get('version', '')}\n"
                f"ID: {info.package_manifest.get('id', 'Unknown')}"
            )
            form.addRow("Sohd package", QLabel(manifest_text))
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class SearchDialog(QDialog):
    pathChosen = pyqtSignal(str)

    def __init__(self, root: Path, parent: QWidget | None = None):
        super().__init__(parent)
        self.root = root
        self.setWindowTitle(f"Search — {root}")
        self.resize(760, 480)
        layout = QVBoxLayout(self)
        self.query = QLineEdit(self)
        self.query.setPlaceholderText("Search file and folder names")
        self.query.returnPressed.connect(self.run_search)
        layout.addWidget(self.query)
        self.results = QListWidget(self)
        self.results.itemDoubleClicked.connect(self.choose)
        layout.addWidget(self.results)
        self.status = QLabel("Enter a search term and press Enter")
        layout.addWidget(self.status)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def run_search(self) -> None:
        self.results.clear()
        matches = search_files(self.root, self.query.text())
        for path in matches:
            item = QListWidgetItem(str(path))
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            self.results.addItem(item)
        self.status.setText(f"{len(matches)} result(s)")

    def choose(self, item: QListWidgetItem) -> None:
        self.pathChosen.emit(item.data(Qt.ItemDataRole.UserRole))
        self.accept()


class FileManager(QMainWindow):
    def __init__(self, self_test: bool = False):
        super().__init__()
        self.self_test = self_test
        self.setWindowTitle(APP_NAME)
        self.resize(1200, 760)
        self.clipboard_paths: list[Path] = []
        self.clipboard_mode = "copy"
        self.model = QFileSystemModel(self)
        self.model.setReadOnly(False)
        self.model.setFilter(QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot)
        self.model.setRootPath(QDir.rootPath())
        self.tree = QTreeView(self)
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(QDir.rootPath()))
        self.tree.setSelectionMode(QTreeView.SelectionMode.ExtendedSelection)
        self.tree.setSortingEnabled(True)
        self.tree.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.tree.doubleClicked.connect(self._double_click)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.path_edit = QLineEdit(self)
        self.path_edit.returnPressed.connect(self.navigate_path)
        self.storage_label = QLabel(self)
        self.search_button = QAction("Search", self, triggered=self.search)
        splitter = QSplitter(self)
        self.sidebar = QListWidget(self)
        self._populate_sidebar()
        self.sidebar.currentRowChanged.connect(self._sidebar_changed)
        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.tree)
        splitter.setStretchFactor(1, 1)
        center = QWidget(self)
        layout = QVBoxLayout(center)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.path_edit)
        layout.addWidget(splitter)
        self.setCentralWidget(center)
        self._build_toolbar()
        self._build_menu()
        self.navigate_path_value(Path.home())
        self.statusBar().showMessage("Ready")
        if self_test:
            QTimer.singleShot(800, self._finish_self_test)

    def _populate_sidebar(self) -> None:
        paths = [Path.home(), Path("/"), Path("/tmp")]
        seen = set()
        for path in paths:
            resolved = path.resolve()
            if resolved not in seen and resolved.exists():
                seen.add(resolved)
                item = QListWidgetItem(f"{resolved}  ({'Home' if resolved == Path.home().resolve() else 'Drive'})")
                item.setData(Qt.ItemDataRole.UserRole, str(resolved))
                self.sidebar.addItem(item)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("File operations", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        def add(text: str, callback, shortcut: str | None = None) -> QAction:
            action = QAction(text, self)
            action.triggered.connect(callback)
            if shortcut:
                action.setShortcut(QKeySequence(shortcut))
            toolbar.addAction(action)
            return action
        add("Up", self.go_up, "Alt+Up")
        add("Back", self.go_back, "Alt+Left")
        add("Forward", self.go_forward, "Alt+Right")
        add("New folder", self.new_folder, "Ctrl+Shift+N")
        add("Rename", self.rename_selected, "F2")
        add("Copy", self.copy_selected, "Ctrl+C")
        add("Cut", self.cut_selected, "Ctrl+X")
        add("Paste", self.paste_selected, "Ctrl+V")
        add("Delete", self.delete_selected, "Delete")
        add("Properties", self.show_properties, "Alt+Enter")
        toolbar.addAction(self.search_button)
        toolbar.addWidget(self.storage_label)

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        file_menu.addAction(QAction("Open", self, shortcut=QKeySequence("Ctrl+O"), triggered=self.open_selected))
        file_menu.addAction(QAction("New folder", self, shortcut=QKeySequence("Ctrl+Shift+N"), triggered=self.new_folder))
        file_menu.addSeparator()
        file_menu.addAction(QAction("Quit", self, shortcut=QKeySequence("Ctrl+Q"), triggered=self.close))
        edit = self.menuBar().addMenu("Edit")
        edit.addAction(QAction("Copy", self, shortcut=QKeySequence("Ctrl+C"), triggered=self.copy_selected))
        edit.addAction(QAction("Cut", self, shortcut=QKeySequence("Ctrl+X"), triggered=self.cut_selected))
        edit.addAction(QAction("Paste", self, shortcut=QKeySequence("Ctrl+V"), triggered=self.paste_selected))
        edit.addAction(QAction("Delete", self, shortcut=QKeySequence("Delete"), triggered=self.delete_selected))
        view = self.menuBar().addMenu("View")
        view.addAction(QAction("Search", self, shortcut=QKeySequence("Ctrl+F"), triggered=self.search))
        view.addAction(QAction("Refresh", self, shortcut=QKeySequence("F5"), triggered=self.refresh))

    def current_directory(self) -> Path:
        return Path(self.path_edit.text()).expanduser().resolve()

    def selected_paths(self) -> list[Path]:
        rows = self.tree.selectionModel().selectedRows(0)
        return [Path(self.model.filePath(index)).resolve() for index in rows]

    def navigate_path_value(self, path: Path) -> None:
        if not path.is_dir():
            path = path.parent
        self.path_edit.setText(str(path))
        self.tree.setRootIndex(self.model.index(str(path)))
        self._update_storage(path)

    def navigate_path(self) -> None:
        path = Path(self.path_edit.text()).expanduser()
        if path.is_dir():
            self.navigate_path_value(path.resolve())
        else:
            self._error("Folder not found", str(path))

    def _update_storage(self, path: Path) -> None:
        try:
            total, used, free = storage_info(path)
            self.storage_label.setText(f"  Storage: {display_size(used)} used / {display_size(total)} total ({display_size(free)} free)  ")
        except OSError:
            self.storage_label.setText("  Storage unavailable  ")

    def _sidebar_changed(self, row: int) -> None:
        if row >= 0:
            self.navigate_path_value(Path(self.sidebar.item(row).data(Qt.ItemDataRole.UserRole)))

    def _double_click(self, index) -> None:
        path = Path(self.model.filePath(index))
        if path.is_dir():
            self.navigate_path_value(path)
        else:
            self.open_path(path)

    def go_up(self) -> None:
        self.navigate_path_value(self.current_directory().parent)

    def go_back(self) -> None:
        self.tree.setRootIndex(self.model.index(self.current_directory().parent))
        self.navigate_path_value(self.current_directory().parent)

    def go_forward(self) -> None:
        self.navigate_path()

    def refresh(self) -> None:
        current = self.current_directory()
        self.model.setRootPath(str(current))
        self.tree.setRootIndex(self.model.index(str(current)))
        self._update_storage(current)

    def new_folder(self) -> None:
        name, ok = QInputDialog.getText(self, "New folder", "Folder name:")
        if ok and name:
            self._run_operation(lambda: create_folder(self.current_directory(), name), "Folder created")

    def rename_selected(self) -> None:
        paths = self.selected_paths()
        if len(paths) != 1:
            self._error("Rename", "Select exactly one file or folder.")
            return
        name, ok = QInputDialog.getText(self, "Rename", "New name:", text=paths[0].name)
        if ok and name:
            self._run_operation(lambda: rename_path(paths[0], name), "Renamed")

    def copy_selected(self) -> None:
        paths = self.selected_paths()
        if paths:
            self.clipboard_paths, self.clipboard_mode = paths, "copy"
            self.statusBar().showMessage(f"Copied {len(paths)} item(s) to the Sohd clipboard", 3000)

    def cut_selected(self) -> None:
        paths = self.selected_paths()
        if paths:
            self.clipboard_paths, self.clipboard_mode = paths, "move"
            self.statusBar().showMessage(f"Marked {len(paths)} item(s) to move", 3000)

    def paste_selected(self) -> None:
        if not self.clipboard_paths:
            self._error("Paste", "The Sohd clipboard is empty.")
            return
        operation = move_items if self.clipboard_mode == "move" else copy_items
        self._run_operation(lambda: operation(self.clipboard_paths, self.current_directory()), "Items pasted")
        if self.clipboard_mode == "move":
            self.clipboard_paths = []

    def delete_selected(self) -> None:
        paths = self.selected_paths()
        if not paths:
            return
        answer = QMessageBox.question(self, "Delete", f"Permanently delete {len(paths)} selected item(s)?")
        if answer == QMessageBox.StandardButton.Yes:
            self._run_operation(lambda: delete_items(paths), "Items deleted")

    def open_selected(self) -> None:
        paths = self.selected_paths()
        if len(paths) == 1:
            self.open_path(paths[0])

    def open_path(self, path: Path) -> None:
        if path.suffix.lower() == ".soh":
            info = properties(path)
            if info.package_manifest:
                manifest = info.package_manifest
                QMessageBox.information(self, "Sohd package", f"{manifest.get('name', path.name)}\nVersion: {manifest.get('version', 'unknown')}\nID: {manifest.get('id', 'unknown')}")
            else:
                self._error("Invalid Sohd package", "This .soh file does not contain a readable manifest.json.")
            return
        try:
            open_path(path)
            self.statusBar().showMessage(f"Opened {path.name}", 3000)
        except (OSError, ValueError) as exc:
            self._error("Open failed", str(exc))

    def show_properties(self) -> None:
        paths = self.selected_paths()
        if len(paths) != 1:
            self._error("Properties", "Select exactly one file or folder.")
            return
        try:
            PropertiesDialog(properties(paths[0]), self).exec()
        except OSError as exc:
            self._error("Properties failed", str(exc))

    def search(self) -> None:
        dialog = SearchDialog(self.current_directory(), self)
        dialog.pathChosen.connect(lambda value: self.navigate_path_value(Path(value).parent))
        dialog.exec()

    def _run_operation(self, operation, success: str) -> None:
        try:
            operation()
            self.refresh()
            self.statusBar().showMessage(success, 3000)
        except (OSError, ValueError, shutil.Error) as exc:
            self._error("File operation failed", str(exc))

    def _error(self, title: str, message: str) -> None:
        QMessageBox.critical(self, title, html.escape(message))

    def _finish_self_test(self) -> None:
        self.close()
        QApplication.instance().quit()


if __name__ == "__main__":
    self_test = "--self-test" in sys.argv
    if self_test:
        sys.argv.remove("--self-test")
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    window = FileManager(self_test)
    window.show()
    raise SystemExit(app.exec())
