from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from browser_core import BrowserState, HOME_URL, normalize_url, security_label


class BrowserCoreTests(unittest.TestCase):
    def test_url_normalization(self) -> None:
        self.assertEqual(normalize_url(""), HOME_URL)
        self.assertEqual(normalize_url("example.com"), "https://example.com")
        self.assertEqual(normalize_url("https://example.com/a"), "https://example.com/a")
        self.assertEqual(normalize_url("sohd://home"), HOME_URL)
        self.assertEqual(normalize_url("Sohd Browser"), "https://duckduckgo.com/?q=Sohd+Browser")

    def test_security_labels(self) -> None:
        self.assertEqual(security_label("https://example.com"), "Secure")
        self.assertEqual(security_label("http://example.com"), "Not secure")
        self.assertEqual(security_label(HOME_URL), "Local")

    def test_bookmarks_history_downloads_persist(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state = BrowserState(directory)
            self.assertTrue(state.toggle_bookmark("Example", "https://example.com"))
            self.assertTrue(state.is_bookmarked("https://example.com"))
            state.add_history("Example", "https://example.com", "2026-09-23T00:00:00+00:00")
            state.add_download("file.txt", "http://localhost/file.txt")
            restored = BrowserState(directory)
            self.assertEqual(restored.bookmarks[0]["title"], "Example")
            self.assertEqual(restored.history[0]["url"], "https://example.com")
            self.assertEqual(restored.downloads[0]["filename"], "file.txt")
            self.assertFalse(restored.toggle_bookmark("Example", "https://example.com"))
            self.assertFalse(restored.is_bookmarked("https://example.com"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
