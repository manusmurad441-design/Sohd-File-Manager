"""Sohd Browser 0.1: a small real desktop browser using Qt WebEngine."""

from __future__ import annotations

import html
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from PyQt6.QtCore import QDateTime, QStandardPaths, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QStyle,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtWebEngineCore import (
    QWebEngineDownloadRequest,
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineSettings,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView

from browser_core import BrowserState, HOME_URL, normalize_url, security_label

APP_NAME = "Sohd Browser"
APP_VERSION = "0.1.0"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def home_html(state: BrowserState) -> str:
    bookmarks = "".join(
        f'<li><a href="{html.escape(item["url"], quote=True)}">{html.escape(item.get("title", item["url"]))}</a></li>'
        for item in state.bookmarks[-8:]
    ) or "<li>No bookmarks yet. Use Ctrl+D to add one.</li>"
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Sohd Browser</title>
<style>
body{{background:#10151d;color:#e7edf5;font:16px system-ui,sans-serif;margin:0}}
main{{max-width:900px;margin:12vh auto;padding:32px}}
h1{{font-size:42px;margin:0 0 8px;color:#78b7ff}} p{{color:#aab6c5}}
section{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:28px}}
article{{background:#182231;border:1px solid #2b4058;border-radius:12px;padding:20px}}
a{{color:#8ac5ff;text-decoration:none}} a:hover{{text-decoration:underline}}
input{{width:100%;box-sizing:border-box;background:#0d1219;border:1px solid #46617d;color:#fff;padding:14px;border-radius:8px;font-size:16px}}
</style></head><body><main>
<h1>Sohd Browser</h1><p>A lightweight browser for the Sohdow ecosystem.</p>
<form action="https://duckduckgo.com/"><input name="q" placeholder="Search the web with DuckDuckGo" autofocus></form>
<section><article><h2>Start browsing</h2><p>Enter a web address or search term in the address bar above. Use Ctrl+L to focus it.</p><p><a href="https://www.example.com/">Open example.com</a></p></article>
<article><h2>Bookmarks</h2><ul>{bookmarks}</ul></article></section>
</main></body></html>"""


def error_html(url: str, reason: str = "The page could not be loaded.") -> str:
    return f"""<!doctype html><meta charset="utf-8"><title>Page unavailable</title>
    <style>body{{font:16px system-ui;background:#10151d;color:#e7edf5;padding:10vh 12vw}}h1{{color:#ff9b9b}}code{{color:#9dcbff;word-break:break-all}}a{{color:#8ac5ff}}</style>
    <h1>Page unavailable</h1><p>{html.escape(reason)}</p><p><code>{html.escape(url)}</code></p>
    <p><a href="sohd://retry">Try again</a> · <a href="sohd://home">Return home</a></p>"""


class BrowserPage(QWebEnginePage):
    internalUrlRequested = pyqtSignal(str)
    certificateRejected = pyqtSignal(str)

    def acceptNavigationRequest(self, url: QUrl, navigation_type: QWebEnginePage.NavigationType, is_main_frame: bool) -> bool:
        if is_main_frame and url.scheme() == "sohd":
            self.internalUrlRequested.emit(url.toString())
            return False
        return super().acceptNavigationRequest(url, navigation_type, is_main_frame)

    def certificateError(self, error) -> bool:
        self.certificateRejected.emit(error.url().toString())
        return False


class BrowserTab(QWidget):
    titleChanged = pyqtSignal(str)
    urlChanged = pyqtSignal(QUrl)
    loadProgress = pyqtSignal(int)
    loadFinished = pyqtSignal(bool)
    internalUrlRequested = pyqtSignal(str)
    downloadRequested = pyqtSignal(object)

    def __init__(self, state: BrowserState, profile: QWebEngineProfile, parent: QWidget | None = None):
        super().__init__(parent)
        self.state = state
        self.view = QWebEngineView(self)
        self.page = BrowserPage(profile, self.view)
        self.view.setPage(self.page)
        self.page.internalUrlRequested.connect(self.internalUrlRequested)
        self.page.certificateRejected.connect(lambda url: self.view.setHtml(error_html(url, "The site certificate was rejected for your safety."), QUrl(url)))
        self.view.titleChanged.connect(self.titleChanged)
        self.view.urlChanged.connect(self._url_changed)
        self.view.loadProgress.connect(self.loadProgress)
        self.view.loadFinished.connect(self._load_finished)
        self.page.windowCloseRequested.connect(self._close_requested)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)

    def _url_changed(self, url: QUrl) -> None:
        self.urlChanged.emit(url)

    def _load_finished(self, ok: bool) -> None:
        if ok:
            self.state.add_history(self.view.title() or self.view.url().toString(), self.view.url().toString(), now_iso())
        self.loadFinished.emit(ok)

    def _close_requested(self) -> None:
        self.parentWidget().deleteLater()

    def navigate(self, url: str) -> None:
        if url == HOME_URL:
            self.view.setHtml(home_html(self.state), QUrl(HOME_URL))
        else:
            self.view.setUrl(QUrl(normalize_url(url)))

    def shutdown(self) -> None:
        self.view.setPage(None)
        self.page.deleteLater()
        self.view.deleteLater()


class ListDialog(QDialog):
    def __init__(self, title: str, entries: list[dict[str, str]], parent: QWidget, empty: str):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(700, 420)
        layout = QVBoxLayout(self)
        self.list = QListWidget(self)
        for entry in reversed(entries):
            item = QListWidgetItem(f"{entry.get('title', entry.get('filename', ''))}\n{entry.get('url', entry.get('status', ''))}")
            item.setData(32, entry.get("url", ""))
            self.list.addItem(item)
        if not entries:
            self.list.addItem(empty)
        layout.addWidget(self.list)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class SohdBrowser(QMainWindow):
    def __init__(self, state: BrowserState, self_test: bool = False):
        super().__init__()
        self.state = state
        self.self_test = self_test
        self.setWindowTitle(APP_NAME)
        self.resize(1280, 820)
        self.profile = QWebEngineProfile("SohdBrowser", self)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
        self.profile.setHttpUserAgent("SohdBrowser/0.1 Sohdow/0.1")
        self.profile.downloadRequested.connect(self._download_requested)
        self.tabs = QTabWidget(self)
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self._current_tab_changed)
        self.setCentralWidget(self.tabs)
        self._build_toolbar()
        self._build_menu()
        self.new_tab(HOME_URL)
        self.statusBar().showMessage("Ready")
        if self_test:
            QTimer.singleShot(1500, self._finish_self_test)

    def _finish_self_test(self) -> None:
        """Close browser-owned pages before ending the Qt event loop."""

        self.close()
        QApplication.instance().quit()

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Navigation", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        def action(icon, text, callback, shortcut=None):
            item = QAction(self.style().standardIcon(icon), text, self)
            item.triggered.connect(callback)
            if shortcut:
                item.setShortcut(QKeySequence(shortcut))
            toolbar.addAction(item)
            return item
        action(QStyle.StandardPixmap.SP_ArrowBack, "Back", lambda: self.current_view().back(), "Alt+Left")
        action(QStyle.StandardPixmap.SP_ArrowForward, "Forward", lambda: self.current_view().forward(), "Alt+Right")
        action(QStyle.StandardPixmap.SP_BrowserReload, "Reload", lambda: self.current_view().reload(), "Ctrl+R")
        action(QStyle.StandardPixmap.SP_DirHomeIcon, "Home", lambda: self.current_tab().navigate(HOME_URL))
        self.address = __import__("PyQt6.QtWidgets", fromlist=["QLineEdit"]).QLineEdit(self)
        self.address.setPlaceholderText("Search or enter web address")
        self.address.returnPressed.connect(self._address_submitted)
        toolbar.addWidget(self.address)
        self.security = QLabel(" Local ", self)
        toolbar.addWidget(self.security)
        self.progress = QProgressBar(self)
        self.progress.setMaximumWidth(120)
        self.progress.setVisible(False)
        toolbar.addWidget(self.progress)

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        new_tab = QAction("New tab", self, shortcut=QKeySequence("Ctrl+T"), triggered=lambda: self.new_tab(HOME_URL))
        file_menu.addAction(new_tab)
        file_menu.addAction(QAction("Close tab", self, shortcut=QKeySequence("Ctrl+W"), triggered=lambda: self.close_tab(self.tabs.currentIndex())))
        file_menu.addSeparator()
        file_menu.addAction(QAction("Quit", self, shortcut=QKeySequence("Ctrl+Q"), triggered=self.close))
        organize = self.menuBar().addMenu("Library")
        organize.addAction(QAction("Bookmark current page", self, shortcut=QKeySequence("Ctrl+D"), triggered=self.toggle_bookmark))
        organize.addAction(QAction("Bookmarks", self, shortcut=QKeySequence("Ctrl+Shift+B"), triggered=self.show_bookmarks))
        organize.addAction(QAction("History", self, shortcut=QKeySequence("Ctrl+H"), triggered=self.show_history))
        organize.addAction(QAction("Downloads", self, triggered=self.show_downloads))
        privacy = self.menuBar().addMenu("Privacy")
        self.javascript_action = QAction("JavaScript enabled", self, checkable=True, checked=True)
        self.javascript_action.triggered.connect(self._toggle_javascript)
        privacy.addAction(self.javascript_action)
        privacy.addAction(QAction("Clear history", self, triggered=self._clear_history))
        privacy.addAction(QAction("Clear cookies and site data", self, triggered=self._clear_site_data))
        privacy.addAction(QAction("About Sohd Browser", self, triggered=self._about))
        focus_address = QAction("Focus address bar", self, shortcut=QKeySequence("Ctrl+L"), triggered=self.address.setFocus)
        self.addAction(focus_address)

    def current_tab(self) -> BrowserTab:
        return self.tabs.currentWidget()

    def current_view(self) -> QWebEngineView:
        return self.current_tab().view

    def new_tab(self, url: str = HOME_URL) -> None:
        tab = BrowserTab(self.state, self.profile, self)
        tab.titleChanged.connect(lambda title, tab_ref=tab: self._set_tab_title(tab_ref, title))
        tab.urlChanged.connect(self._url_changed)
        tab.loadProgress.connect(self._progress)
        tab.loadFinished.connect(self._loaded)
        tab.internalUrlRequested.connect(self._internal_url)
        index = self.tabs.addTab(tab, "New tab")
        self.tabs.setCurrentIndex(index)
        tab.navigate(url)

    def close_tab(self, index: int) -> None:
        if self.tabs.count() == 1:
            self.close()
            return
        widget = self.tabs.widget(index)
        self.tabs.removeTab(index)
        widget.deleteLater()

    def _set_tab_title(self, tab: BrowserTab, title: str) -> None:
        index = self.tabs.indexOf(tab)
        if index >= 0:
            self.tabs.setTabText(index, (title or "New tab")[:28])

    def _current_tab_changed(self, _: int) -> None:
        if self.tabs.currentWidget():
            self._url_changed(self.tabs.currentWidget().view.url())

    def _url_changed(self, url: QUrl) -> None:
        if self.sender() is not None and self.tabs.currentWidget() is not self.sender():
            return
        self.address.setText("" if url.toString() == HOME_URL else url.toString())
        self.security.setText(" " + security_label(url.toString()) + " ")

    def _address_submitted(self) -> None:
        self.current_tab().navigate(self.address.text())

    def toggle_bookmark(self) -> None:
        current = self.current_view()
        url = current.url().toString()
        if not url or url.startswith("sohd://"):
            self.statusBar().showMessage("The home page cannot be bookmarked", 3000)
            return
        added = self.state.toggle_bookmark(current.title() or url, url)
        self.statusBar().showMessage("Bookmark added" if added else "Bookmark removed", 3000)

    def _progress(self, value: int) -> None:
        self.progress.setVisible(value < 100)
        self.progress.setValue(value)

    def _loaded(self, ok: bool) -> None:
        if not ok and self.current_view().url().scheme() in {"http", "https"}:
            self.current_view().setHtml(error_html(self.current_view().url().toString()), self.current_view().url())
        self.statusBar().showMessage("Loaded" if ok else "Load failed", 3000)

    def _internal_url(self, url: str) -> None:
        if url == "sohd://home":
            self.current_tab().navigate(HOME_URL)
        elif url == "sohd://retry":
            self.current_view().reload()

    def _toggle_javascript(self, enabled: bool) -> None:
        self.profile.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, enabled)
        self.statusBar().showMessage("JavaScript " + ("enabled" if enabled else "disabled"), 3000)

    def _download_requested(self, download: QWebEngineDownloadRequest) -> None:
        suggested = download.downloadFileName() or "download"
        automated_directory = os.environ.get("SOHD_BROWSER_TEST_DOWNLOAD_DIR")
        if automated_directory:
            target = str(Path(automated_directory).expanduser().resolve() / suggested)
        else:
            target, _ = QFileDialog.getSaveFileName(self, "Save download", str(self.state.downloads_dir / suggested))
        if not target:
            download.cancel()
            return
        path = Path(target).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        download.setDownloadDirectory(str(path.parent))
        download.setDownloadFileName(path.name)
        self.state.add_download(path.name, download.url().toString(), "started")
        download.stateChanged.connect(lambda state, item=download, name=path.name: self._download_state(state, item, name))
        download.accept()

    def _download_state(self, state, download, name: str) -> None:
        if state == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
            self.state.add_download(name, download.url().toString(), "completed")
            self.statusBar().showMessage(f"Downloaded {name}", 5000)
        elif state == QWebEngineDownloadRequest.DownloadState.DownloadInterrupted:
            self.state.add_download(name, download.url().toString(), "interrupted")

    def _open_list(self, dialog: ListDialog) -> None:
        dialog.list.itemDoubleClicked.connect(lambda item: self._open_list_url(item.data(32), dialog))
        dialog.exec()

    def _open_list_url(self, url: str, dialog: QDialog) -> None:
        if url:
            self.address.setText(url)
            self.current_tab().navigate(url)
            dialog.accept()

    def show_bookmarks(self) -> None:
        self._open_list(ListDialog("Bookmarks", self.state.bookmarks, self, "No bookmarks yet."))

    def show_history(self) -> None:
        self._open_list(ListDialog("History", self.state.history, self, "No history yet."))

    def show_downloads(self) -> None:
        self._open_list(ListDialog("Downloads", self.state.downloads, self, "No downloads yet."))

    def _clear_history(self) -> None:
        self.state.clear_history()
        QMessageBox.information(self, "History cleared", "Sohd Browser history has been cleared.")

    def _clear_site_data(self) -> None:
        self.profile.clearHttpCache()
        self.profile.cookieStore().deleteAllCookies()
        QMessageBox.information(self, "Site data cleared", "Cached files and cookies have been cleared.")

    def _about(self) -> None:
        QMessageBox.about(self, "About Sohd Browser", f"{APP_NAME} {APP_VERSION}\nA free and open-source-friendly Sohdow application.")

    def closeEvent(self, event) -> None:
        for index in range(self.tabs.count()):
            tab = self.tabs.widget(index)
            if isinstance(tab, BrowserTab):
                tab.shutdown()
        self.tabs.clear()
        QApplication.processEvents()
        super().closeEvent(event)


def data_directory() -> Path:
    configured = os.environ.get("SOHD_BROWSER_DATA_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    return Path(base or "~/.local/share/sohd-browser").expanduser().resolve()


def main() -> int:
    self_test = "--self-test" in sys.argv
    if self_test:
        sys.argv.remove("--self-test")
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    state = BrowserState(data_directory())
    window = SohdBrowser(state, self_test=self_test)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
