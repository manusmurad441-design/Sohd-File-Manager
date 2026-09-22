from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from editor_core import language_for_path, load_recent, load_utf8, record_recent, save_utf8


class EditorCoreTests(unittest.TestCase):
    def test_utf8_round_trip_and_atomic_save(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "notes.txt"
            text = "Sohdow — مرحبًا\nline two\n"
            save_utf8(path, text)
            self.assertEqual(load_utf8(path), text)
            self.assertFalse((path.parent / ".notes.txt.sohd-tmp").exists())

    def test_recent_files_are_deduplicated_and_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            old = os.environ.get("SOHD_EDITOR_DATA_DIR")
            os.environ["SOHD_EDITOR_DATA_DIR"] = directory
            try:
                paths = []
                for index in range(3):
                    path = Path(directory) / f"file{index}.txt"
                    path.write_text(str(index), encoding="utf-8")
                    paths.append(path)
                    record_recent(path)
                self.assertEqual(Path(load_recent()[0]), paths[-1].resolve())
                record_recent(paths[0])
                self.assertEqual(Path(load_recent()[0]), paths[0].resolve())
                self.assertEqual(len(load_recent()), 3)
            finally:
                if old is None:
                    os.environ.pop("SOHD_EDITOR_DATA_DIR", None)
                else:
                    os.environ["SOHD_EDITOR_DATA_DIR"] = old

    def test_language_detection(self):
        self.assertEqual(language_for_path("main.py"), "Python")
        self.assertEqual(language_for_path("manifest.json"), "JSON")
        self.assertEqual(language_for_path("README.md"), "Markdown")
        self.assertEqual(language_for_path("unknown.xyz"), "Plain text")


if __name__ == "__main__":
    unittest.main(verbosity=2)
