"""Testable document and recent-file services for Sohd Document Editor 0.1."""

from __future__ import annotations

import json
import os
from pathlib import Path

MAX_RECENT = 20


def load_utf8(path: str | Path) -> str:
    return Path(path).expanduser().resolve().read_text(encoding="utf-8")


def save_utf8(path: str | Path, text: str) -> Path:
    target = Path(path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.sohd-tmp")
    temporary.write_text(text, encoding="utf-8", newline="")
    os.replace(temporary, target)
    return target


def recent_path() -> Path:
    custom = os.environ.get("SOHD_EDITOR_DATA_DIR")
    if custom:
        return Path(custom).expanduser().resolve() / "recent.json"
    return Path(os.environ.get("XDG_STATE_HOME", "~/.local/state")).expanduser().resolve() / "sohd-document-editor" / "recent.json"


def load_recent() -> list[str]:
    try:
        value = json.loads(recent_path().read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return []
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and Path(item).is_file()][:MAX_RECENT]


def record_recent(path: str | Path) -> list[str]:
    target = str(Path(path).expanduser().resolve())
    values = [target] + [item for item in load_recent() if item != target]
    values = values[:MAX_RECENT]
    destination = recent_path()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(json.dumps(values, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, destination)
    return values


def language_for_path(path: str | Path | None) -> str:
    suffix = Path(path).suffix.lower() if path else ""
    return {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".json": "JSON",
        ".md": "Markdown",
        ".html": "HTML",
        ".htm": "HTML",
        ".css": "CSS",
        ".xml": "XML",
        ".sh": "Shell",
        ".toml": "TOML",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".c": "C/C++",
        ".h": "C/C++",
        ".cpp": "C/C++",
    }.get(suffix, "Plain text")
