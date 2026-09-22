"""Non-GUI browser services used by Sohd Browser 0.1."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, urlparse


HOME_URL = "sohd://home"
MAX_HISTORY = 500
MAX_BOOKMARKS = 500
_URL_SCHEMES = {"http", "https", "file", "sohd"}


def normalize_url(text: str) -> str:
    """Turn address-bar text into a navigable URL without pretending to be a URL."""

    value = text.strip()
    if not value:
        return HOME_URL
    parsed = urlparse(value)
    if parsed.scheme.lower() in _URL_SCHEMES:
        return value
    if " " not in value and "." in value and not value.startswith("."):
        return "https://" + value
    return "https://duckduckgo.com/?q=" + quote_plus(value)


def security_label(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme == "https":
        return "Secure"
    if parsed.scheme == "sohd":
        return "Local"
    if parsed.scheme == "http":
        return "Not secure"
    if parsed.scheme == "file":
        return "Local file"
    return "Unknown"


def is_web_url(url: str) -> bool:
    return urlparse(url).scheme in {"http", "https"}


@dataclass
class HistoryEntry:
    title: str
    url: str
    visited_at: str


class BrowserState:
    """Small JSON-backed profile state with bounded history and bookmarks."""

    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir).expanduser().resolve()
        self.state_path = self.data_dir / "state.json"
        self.downloads_dir = self.data_dir / "downloads"
        self.bookmarks: list[dict[str, str]] = []
        self.history: list[dict[str, str]] = []
        self.downloads: list[dict[str, str]] = []
        self.load()

    def load(self) -> None:
        try:
            document = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, UnicodeDecodeError, json.JSONDecodeError):
            document = {}
        if not isinstance(document, dict):
            document = {}
        self.bookmarks = self._clean_entries(document.get("bookmarks"), MAX_BOOKMARKS)
        self.history = self._clean_entries(document.get("history"), MAX_HISTORY)
        self.downloads = self._clean_entries(document.get("downloads"), MAX_HISTORY)

    @staticmethod
    def _clean_entries(value: Any, limit: int) -> list[dict[str, str]]:
        if not isinstance(value, list):
            return []
        result = []
        for item in value[-limit:]:
            if isinstance(item, dict) and isinstance(item.get("url"), str):
                result.append({key: str(value) for key, value in item.items() if isinstance(key, str) and isinstance(value, (str, int, float))})
        return result

    def save(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        temporary = self.state_path.with_suffix(".tmp")
        document = {"bookmarks": self.bookmarks[-MAX_BOOKMARKS:], "history": self.history[-MAX_HISTORY:], "downloads": self.downloads[-MAX_HISTORY:]}
        temporary.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(self.state_path)

    def add_history(self, title: str, url: str, visited_at: str) -> None:
        if not is_web_url(url) and url != HOME_URL:
            return
        self.history.append({"title": title or url, "url": url, "visited_at": visited_at})
        self.history = self.history[-MAX_HISTORY:]
        self.save()

    def toggle_bookmark(self, title: str, url: str) -> bool:
        existing = next((item for item in self.bookmarks if item.get("url") == url), None)
        if existing:
            self.bookmarks.remove(existing)
            self.save()
            return False
        self.bookmarks.append({"title": title or url, "url": url})
        self.bookmarks = self.bookmarks[-MAX_BOOKMARKS:]
        self.save()
        return True

    def is_bookmarked(self, url: str) -> bool:
        return any(item.get("url") == url for item in self.bookmarks)

    def add_download(self, filename: str, url: str, status: str = "completed") -> None:
        self.downloads.append({"filename": filename, "url": url, "status": status})
        self.downloads = self.downloads[-MAX_HISTORY:]
        self.save()

    def clear_history(self) -> None:
        self.history.clear()
        self.save()
