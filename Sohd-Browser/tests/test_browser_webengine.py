from __future__ import annotations

import os
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PyQt6.QtCore import QEventLoop, QTimer, QUrl
from PyQt6.QtWidgets import QApplication

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "app"))
from main import SohdBrowser
from browser_core import BrowserState


class BrowserHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/download.txt":
            body = b"Sohd Browser download test\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Disposition", "attachment; filename=download.txt")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        body = b'''<!doctype html><title>Sohd Test Page</title>
        <h1 id="heading">Sohd Browser navigation test</h1>
        <a id="download" href="/download.txt">Download test file</a>'''
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass


class EmbeddedBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([sys.argv[0]])
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), BrowserHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}/"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join(timeout=2)

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.downloads = Path(self.directory.name) / "downloads"
        os.environ["SOHD_BROWSER_DATA_DIR"] = self.directory.name
        os.environ["SOHD_BROWSER_TEST_DOWNLOAD_DIR"] = str(self.downloads)
        self.browser = SohdBrowser(BrowserState(self.directory.name))
        self.browser.show()

    def tearDown(self):
        self.browser.close()
        self.directory.cleanup()
        os.environ.pop("SOHD_BROWSER_DATA_DIR", None)
        os.environ.pop("SOHD_BROWSER_TEST_DOWNLOAD_DIR", None)
        self.app.processEvents()

    def wait_for(self, predicate, timeout=8000):
        deadline = time.monotonic() + timeout / 1000
        while not predicate() and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.01)
        self.assertTrue(predicate(), "timed out waiting for browser event")

    def test_navigation_tabs_bookmark_history_download_and_error_page(self):
        tab = self.browser.current_tab()
        finished = []
        tab.loadFinished.connect(finished.append)
        tab.navigate(self.base_url)
        self.wait_for(lambda: finished and finished[-1] is True)
        self.assertEqual(tab.view.title(), "Sohd Test Page")
        self.assertIn("Sohd Browser navigation test", self._html(tab))
        self.assertEqual(tab.view.url().toString(), self.base_url)
        self.assertTrue(self.browser.state.history)

        self.browser.toggle_bookmark()
        self.assertTrue(self.browser.state.is_bookmarked(self.base_url))
        self.browser.toggle_bookmark()
        self.assertFalse(self.browser.state.is_bookmarked(self.base_url))
        self.browser.toggle_bookmark()

        self.browser.new_tab(self.base_url)
        self.assertEqual(self.browser.tabs.count(), 2)
        self.browser.close_tab(1)
        self.assertEqual(self.browser.tabs.count(), 1)

        tab.view.page().runJavaScript("document.getElementById('download').click();")
        self.wait_for(lambda: (self.downloads / "download.txt").is_file(), timeout=10000)
        self.assertEqual((self.downloads / "download.txt").read_text(), "Sohd Browser download test\n")

        broken = f"http://127.0.0.1:{self.server.server_port + 1}/missing"
        tab.navigate(broken)
        self.wait_for(lambda: "Page unavailable" in self._html(tab), timeout=10000)

    @staticmethod
    def _html(tab):
        result = []
        loop = QEventLoop()
        tab.view.page().toHtml(lambda content: (result.append(content), loop.quit()))
        QTimer.singleShot(100, loop.quit)
        loop.exec()
        return result[0] if result else ""


if __name__ == "__main__":
    unittest.main(verbosity=2)
