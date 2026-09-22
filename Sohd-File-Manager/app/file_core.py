"""Filesystem operations for Sohd File Manager 0.1."""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class FileProperties:
    path: Path
    name: str
    kind: str
    size: int
    modified: str
    permissions: str
    package_manifest: dict | None = None


def display_size(value: int) -> str:
    size = float(value)
    for suffix in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or suffix == "TB":
            return f"{size:.1f} {suffix}" if suffix != "B" else f"{int(size)} B"
        size /= 1024
    return f"{value} B"


def package_manifest(path: Path) -> dict | None:
    if path.suffix.lower() != ".soh" or not path.is_file():
        return None
    try:
        with zipfile.ZipFile(path) as archive:
            data = json.loads(archive.read("manifest.json").decode("utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, KeyError, UnicodeDecodeError, json.JSONDecodeError, zipfile.BadZipFile):
        return None


def properties(path: str | Path) -> FileProperties:
    target = Path(path).expanduser().resolve()
    info = target.stat()
    if target.is_dir():
        kind = "Folder"
    elif target.suffix.lower() == ".soh":
        kind = "Sohd application package"
    else:
        kind = "File"
    return FileProperties(
        path=target,
        name=target.name or str(target),
        kind=kind,
        size=info.st_size if target.is_file() else 0,
        modified=datetime.fromtimestamp(info.st_mtime).astimezone().isoformat(timespec="seconds"),
        permissions=stat.filemode(info.st_mode),
        package_manifest=package_manifest(target),
    )


def _ensure_not_inside(source: Path, destination_directory: Path) -> None:
    if source == destination_directory or destination_directory.is_relative_to(source):
        raise ValueError("A folder cannot be copied or moved into itself")


def create_folder(parent: str | Path, name: str) -> Path:
    parent_path = Path(parent).expanduser().resolve()
    clean_name = name.strip()
    if not clean_name or clean_name in {".", ".."} or "/" in clean_name or "\\" in clean_name:
        raise ValueError("Folder name must be a single non-empty path component")
    target = parent_path / clean_name
    target.mkdir()
    return target


def rename_path(path: str | Path, new_name: str) -> Path:
    source = Path(path).expanduser().resolve()
    clean_name = new_name.strip()
    if not clean_name or clean_name in {".", ".."} or "/" in clean_name or "\\" in clean_name:
        raise ValueError("Name must be a single non-empty path component")
    target = source.parent / clean_name
    if target.exists():
        raise FileExistsError(target)
    return source.rename(target)


def copy_items(sources: Iterable[str | Path], destination_directory: str | Path) -> list[Path]:
    destination = Path(destination_directory).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    results = []
    for source_value in sources:
        source = Path(source_value).expanduser().resolve()
        if not source.exists():
            raise FileNotFoundError(source)
        _ensure_not_inside(source, destination)
        target = destination / source.name
        if target.exists():
            raise FileExistsError(target)
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)
        results.append(target)
    return results


def move_items(sources: Iterable[str | Path], destination_directory: str | Path) -> list[Path]:
    destination = Path(destination_directory).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    results = []
    for source_value in sources:
        source = Path(source_value).expanduser().resolve()
        if not source.exists():
            raise FileNotFoundError(source)
        _ensure_not_inside(source, destination)
        target = destination / source.name
        if target.exists():
            raise FileExistsError(target)
        results.append(Path(shutil.move(str(source), str(target))).resolve())
    return results


def delete_items(sources: Iterable[str | Path]) -> None:
    for source_value in sources:
        source = Path(source_value).expanduser().resolve()
        if source.is_dir():
            shutil.rmtree(source)
        elif source.exists():
            source.unlink()


def search_files(root: str | Path, query: str) -> list[Path]:
    base = Path(root).expanduser().resolve()
    needle = query.casefold().strip()
    if not needle:
        return []
    matches: list[Path] = []
    for current, directories, filenames in os.walk(base, topdown=True, followlinks=False):
        directories[:] = [name for name in directories if not (Path(current) / name).is_symlink()]
        for name in [*directories, *filenames]:
            if needle in name.casefold():
                matches.append(Path(current) / name)
    return matches


def open_path(path: str | Path) -> None:
    target = Path(path).expanduser().resolve()
    if not target.exists():
        raise FileNotFoundError(target)
    if target.suffix.lower() == ".soh":
        return
    subprocess.Popen(["xdg-open", str(target)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def storage_info(path: str | Path) -> tuple[int, int, int]:
    usage = shutil.disk_usage(Path(path).expanduser().resolve())
    return usage.total, usage.used, usage.free
