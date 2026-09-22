from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from settings_core import (
    installed_applications,
    load_settings,
    save_settings,
    screen_information,
    storage_information,
    system_information,
)


class FakeScreen:
    def name(self):
        return "Test Display"

    def geometry(self):
        return type("Rect", (), {"width": lambda self: 1920, "height": lambda self: 1080})()

    def availableGeometry(self):
        return type("Rect", (), {"width": lambda self: 1920, "height": lambda self: 1040})()

    def refreshRate(self):
        return 60.0

    def devicePixelRatio(self):
        return 1.0


class SettingsCoreTests(unittest.TestCase):
    def test_settings_persist_to_local_file(self):
        with tempfile.TemporaryDirectory() as directory:
            old = os.environ.get("SOHD_SETTINGS_DIR")
            os.environ["SOHD_SETTINGS_DIR"] = directory
            try:
                path = save_settings({"theme": "Dark", "language": "en", "font_scale": 110})
                self.assertTrue(path.is_file())
                self.assertEqual(load_settings()["theme"], "Dark")
                self.assertEqual(json.loads(path.read_text())["font_scale"], 110)
            finally:
                if old is None:
                    os.environ.pop("SOHD_SETTINGS_DIR", None)
                else:
                    os.environ["SOHD_SETTINGS_DIR"] = old

    def test_real_system_storage_and_display_data(self):
        system = system_information()
        self.assertTrue(system["Python"])
        usage = storage_information("/")
        self.assertGreater(usage["total"], 0)
        self.assertGreaterEqual(usage["total"], usage["used"])
        display = screen_information(FakeScreen())
        self.assertEqual(display["Resolution"], "1920 × 1080")
        self.assertEqual(display["Refresh rate"], "60.00 Hz")

    def test_installed_app_registry_is_safe_when_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(installed_applications(directory), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
