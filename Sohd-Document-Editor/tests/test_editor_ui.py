from __future__ import annotations

import os
import tempfile
import sys
import unittest
from pathlib import Path

from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import QApplication

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "app"))
from main import FindReplaceDialog, TextEditor


class EditorUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([sys.argv[0]])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        os.environ["SOHD_EDITOR_DATA_DIR"] = self.temp.name
        self.path = Path(self.temp.name) / "document.py"
        self.path.write_text("hello hello\n", encoding="utf-8")
        self.window = TextEditor(str(self.path))
        self.window.show()
        self.app.processEvents()

    def tearDown(self):
        self.window.close()
        self.app.processEvents()
        self.temp.cleanup()
        os.environ.pop("SOHD_EDITOR_DATA_DIR", None)

    def test_open_edit_save_undo_redo_and_replace(self):
        self.assertEqual(self.window.editor.toPlainText(), "hello hello\n")
        self.window.editor.moveCursor(QTextCursor.MoveOperation.End)
        self.window.editor.insertPlainText("tail")
        self.assertTrue(self.window.editor.document().isModified())
        self.window.editor.undo()
        self.window.editor.redo()
        self.assertTrue(self.window.save_file())
        self.assertEqual(self.path.read_text(encoding="utf-8"), "hello hello\ntail")
        dialog = FindReplaceDialog(self.window.editor, self.window)
        dialog.find.setText("hello")
        dialog.replace.setText("Sohd")
        dialog.replace_all()
        self.assertEqual(self.window.editor.toPlainText(), "Sohd Sohd\ntail")


if __name__ == "__main__":
    unittest.main(verbosity=2)
