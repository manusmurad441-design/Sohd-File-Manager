"""Sohd Document Editor 0.1 native Qt application."""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

from PyQt6.QtCore import QRegularExpression, Qt, QTimer
from PyQt6.QtGui import QAction, QColor, QFont, QKeySequence, QPainter, QSyntaxHighlighter, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from editor_core import language_for_path, load_recent, load_utf8, record_recent, save_utf8

APP_NAME = "Sohd Document Editor"
APP_VERSION = "0.1.0"


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return self.editor.line_number_area_width(), 0

    def paintEvent(self, event):
        self.editor.paint_line_numbers(event)


class CodeHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.rules = []
        for pattern, color, bold in [
            (r"\b(if|else|elif|for|while|return|class|def|import|from|try|except|with|as|in|True|False|None|function|const|let|var|new|public|private)\b", "#8b5cf6", True),
            (r"\b[0-9]+(?:\.[0-9]+)?\b", "#0891b2", False),
            (r"#[^\n]*", "#6b7280", False),
            (r"//[^\n]*", "#6b7280", False),
            (r"\b[A-Za-z_][A-Za-z0-9_]*(?=\s*\()", "#0f766e", False),
            (r"\"[^\"\n]*\"|'[^'\n]*'", "#b45309", False),
        ]:
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))
            fmt.setFontWeight(QFont.Weight.Bold if bold else QFont.Weight.Normal)
            self.rules.append((QRegularExpression(pattern), fmt))

    def highlightBlock(self, text):
        for expression, fmt in self.rules:
            match = expression.match(text)
            while match.hasMatch():
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)
                match = expression.match(text, match.capturedEnd())


class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.update_line_number_width(0)
        self.highlight_current_line()
        self.highlighter = CodeHighlighter(self.document())
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(" "))

    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        return 14 + self.fontMetrics().horizontalAdvance("9") * digits

    def update_line_number_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        rect = self.contentsRect()
        self.line_number_area.setGeometry(rect.left(), rect.top(), self.line_number_area_width(), rect.height())

    def paint_line_numbers(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#f2f4f7"))
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.setPen(QColor("#7a8696"))
                painter.drawText(0, top, self.line_number_area.width() - 6, self.fontMetrics().height(), Qt.AlignmentFlag.AlignRight, str(block_number + 1))
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def highlight_current_line(self):
        selection = QTextEdit.ExtraSelection()
        selection.format.setBackground(QColor("#fffbe6"))
        selection.format.setProperty(QTextCharFormat.Property.FullWidthSelection, True)
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        self.setExtraSelections([selection])


class FindReplaceDialog(QDialog):
    def __init__(self, editor: CodeEditor, parent=None):
        super().__init__(parent)
        self.editor = editor
        self.setWindowTitle("Find and Replace")
        self.resize(520, 150)
        layout = QFormLayout(self)
        self.find = QLineEdit(self)
        self.replace = QLineEdit(self)
        layout.addRow("Find", self.find)
        layout.addRow("Replace with", self.replace)
        buttons = QHBoxLayout()
        for label, callback in [("Find next", self.find_next), ("Replace", self.replace_one), ("Replace all", self.replace_all)]:
            button = QPushButton(label, self)
            button.clicked.connect(callback)
            buttons.addWidget(button)
        layout.addRow(buttons)
        close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close.rejected.connect(self.reject)
        layout.addRow(close)

    def find_next(self):
        needle = self.find.text()
        if not needle:
            return
        if not self.editor.find(needle):
            cursor = self.editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self.editor.setTextCursor(cursor)
            self.editor.find(needle)

    def replace_one(self):
        cursor = self.editor.textCursor()
        if cursor.hasSelection() and cursor.selectedText() == self.find.text():
            cursor.insertText(self.replace.text())
        self.find_next()

    def replace_all(self):
        needle = self.find.text()
        if not needle:
            return
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()
        text = self.editor.toPlainText().replace(needle, self.replace.text())
        self.editor.setPlainText(text)
        cursor.endEditBlock()


class TextEditor(QMainWindow):
    def __init__(self, path: str | None = None, self_test: bool = False):
        super().__init__()
        self.self_test = self_test
        self.path: Path | None = None
        self.editor = CodeEditor()
        self.editor.document().modificationChanged.connect(self._modified_changed)
        self.setCentralWidget(self.editor)
        self.setAcceptDrops(True)
        self._build_toolbar()
        self._build_menus()
        self._load_recent_menu()
        self._update_title()
        if path:
            self.open_path(path)
        else:
            self.editor.setPlainText("")
        if self_test:
            QTimer.singleShot(700, self._finish_self_test)

    def _build_toolbar(self):
        toolbar = QToolBar("Editor", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        for text, callback in [("New", self.new_file), ("Open", self.open_dialog), ("Save", self.save_file), ("Find", self.show_find_replace)]:
            action = QAction(text, self)
            action.triggered.connect(callback)
            toolbar.addAction(action)
        self.statusBar().showMessage("Ready")

    def _build_menus(self):
        file_menu = self.menuBar().addMenu("File")
        file_menu.addAction(QAction("New", self, shortcut=QKeySequence("Ctrl+N"), triggered=self.new_file))
        file_menu.addAction(QAction("Open…", self, shortcut=QKeySequence("Ctrl+O"), triggered=self.open_dialog))
        file_menu.addAction(QAction("Save", self, shortcut=QKeySequence("Ctrl+S"), triggered=self.save_file))
        file_menu.addAction(QAction("Save As…", self, shortcut=QKeySequence("Ctrl+Shift+S"), triggered=self.save_as))
        self.recent_menu = file_menu.addMenu("Recent files")
        file_menu.addSeparator()
        file_menu.addAction(QAction("Quit", self, shortcut=QKeySequence("Ctrl+Q"), triggered=self.close))
        edit = self.menuBar().addMenu("Edit")
        edit.addAction(QAction("Undo", self, shortcut=QKeySequence("Ctrl+Z"), triggered=self.editor.undo))
        edit.addAction(QAction("Redo", self, shortcut=QKeySequence("Ctrl+Y"), triggered=self.editor.redo))
        edit.addAction(QAction("Find and replace…", self, shortcut=QKeySequence("Ctrl+H"), triggered=self.show_find_replace))
        edit.addAction(QAction("Select all", self, shortcut=QKeySequence("Ctrl+A"), triggered=self.editor.selectAll))
        view = self.menuBar().addMenu("View")
        view.addAction(QAction("Zoom in", self, shortcut=QKeySequence("Ctrl++"), triggered=lambda: self.editor.zoomIn(1)))
        view.addAction(QAction("Zoom out", self, shortcut=QKeySequence("Ctrl+-"), triggered=lambda: self.editor.zoomOut(1)))

    def _load_recent_menu(self):
        self.recent_menu.clear()
        recent = load_recent()
        if not recent:
            action = self.recent_menu.addAction("No recent files")
            action.setEnabled(False)
            return
        for value in recent:
            action = self.recent_menu.addAction(value)
            action.triggered.connect(lambda checked=False, path=value: self.open_path(path))

    def _modified_changed(self, modified: bool):
        self._update_title()

    def _update_title(self):
        name = self.path.name if self.path else "Untitled"
        marker = "*" if self.editor.document().isModified() else ""
        language = language_for_path(self.path)
        self.setWindowTitle(f"{marker}{name} — {APP_NAME}")
        self.statusBar().showMessage(f"{language} | UTF-8 | Line {self.editor.textCursor().blockNumber() + 1}, Column {self.editor.textCursor().columnNumber() + 1}")

    def new_file(self):
        if not self._confirm_discard():
            return
        self.path = None
        self.editor.clear()
        self.editor.document().setModified(False)
        self._update_title()

    def open_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open text file", str(Path.home()), "Text and source files (*)")
        if path:
            self.open_path(path)

    def open_path(self, value: str | Path):
        path = Path(value).expanduser().resolve()
        if not path.is_file():
            self._error("Open failed", f"File does not exist: {path}")
            return False
        if not self._confirm_discard():
            return False
        try:
            text = load_utf8(path)
        except (OSError, UnicodeDecodeError) as exc:
            self._error("Open failed", f"Could not read UTF-8 text: {exc}")
            return False
        self.editor.setPlainText(text)
        self.editor.document().setModified(False)
        self.path = path
        record_recent(path)
        self._load_recent_menu()
        self._update_title()
        return True

    def save_file(self):
        if self.path is None:
            return self.save_as()
        try:
            save_utf8(self.path, self.editor.toPlainText())
        except OSError as exc:
            self._error("Save failed", str(exc))
            return False
        self.editor.document().setModified(False)
        record_recent(self.path)
        self._load_recent_menu()
        self._update_title()
        self.statusBar().showMessage(f"Saved {self.path}", 3000)
        return True

    def save_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save text file", str(self.path or Path.home() / "Untitled.txt"), "Text files (*)")
        if not path:
            return False
        self.path = Path(path).expanduser().resolve()
        return self.save_file()

    def show_find_replace(self):
        dialog = FindReplaceDialog(self.editor, self)
        dialog.find.setFocus()
        dialog.exec()

    def _confirm_discard(self):
        if not self.editor.document().isModified():
            return True
        answer = QMessageBox.question(self, "Unsaved changes", "Save changes before continuing?", QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
        if answer == QMessageBox.StandardButton.Save:
            return self.save_file()
        return answer == QMessageBox.StandardButton.Discard

    def closeEvent(self, event):
        if self._confirm_discard():
            event.accept()
        else:
            event.ignore()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            self.open_path(urls[0].toLocalFile())
            event.acceptProposedAction()

    def _error(self, title: str, message: str):
        QMessageBox.critical(self, title, html.escape(message))

    def _finish_self_test(self):
        self.close()
        QApplication.instance().quit()


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    self_test = "--self-test" in args
    args = [item for item in args if item != "--self-test"]
    app = QApplication([sys.argv[0]])
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    window = TextEditor(args[0] if args else None, self_test)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
