from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from file_core import (
    copy_items,
    create_folder,
    delete_items,
    move_items,
    package_manifest,
    properties,
    rename_path,
    search_files,
    storage_info,
)


class FileManagerCoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "Documents").mkdir()
        (self.root / "Documents" / "notes.txt").write_text("notes", encoding="utf-8")
        (self.root / "photo.png").write_bytes(b"png")

    def tearDown(self):
        self.temp.cleanup()

    def test_create_rename_copy_move_delete(self):
        created = create_folder(self.root, "New Folder")
        self.assertTrue(created.is_dir())
        renamed = rename_path(created, "Renamed Folder")
        self.assertTrue(renamed.is_dir())
        copied = copy_items([self.root / "Documents" / "notes.txt"], renamed)
        self.assertEqual(copied[0].read_text(encoding="utf-8"), "notes")
        moved = move_items([self.root / "photo.png"], renamed)
        self.assertTrue(moved[0].is_file())
        delete_items([renamed])
        self.assertFalse(renamed.exists())

    def test_search_properties_and_storage(self):
        results = search_files(self.root, "notes")
        self.assertEqual(results, [self.root / "Documents" / "notes.txt"])
        info = properties(self.root / "photo.png")
        self.assertEqual(info.kind, "File")
        self.assertEqual(info.size, 3)
        total, used, free = storage_info(self.root)
        self.assertGreater(total, 0)
        self.assertGreater(used, 0)
        self.assertGreater(free, 0)
        self.assertLessEqual(used + free, total)

    def test_soh_manifest_support(self):
        manifest = {"format_version": "0.1", "id": "org.sohdow.test", "name": "Test", "version": "0.1.0"}
        package = self.root / "Test.soh"
        with zipfile.ZipFile(package, "w") as archive:
            archive.writestr("manifest.json", json.dumps(manifest))
        self.assertEqual(package_manifest(package)["id"], "org.sohdow.test")
        self.assertEqual(properties(package).kind, "Sohd application package")


if __name__ == "__main__":
    unittest.main(verbosity=2)
