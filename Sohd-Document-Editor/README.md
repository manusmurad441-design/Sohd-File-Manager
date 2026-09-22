# Sohd Document Editor 0.1

Sohd Document Editor is the fourth official Sohdow application. It is a native PyQt6 editor for UTF-8 text and source files. It is lightweight, local, and self-contained apart from the host-provided PyQt6/Qt runtime.

## Features

The editor supports new documents, opening existing files, editing, UTF-8 load and save, Save As, atomic file replacement, recent files, undo and redo, line numbers, current-line highlighting, basic extension-aware syntax highlighting, find next, replace one, replace all, drag-and-drop opening, command-line opening, keyboard shortcuts, and unsaved-change confirmation.

The application accepts a file path as its first command-line argument. This is the concrete integration path for opening a file from a Sohdow File Manager association or launcher. The current Sohd App Format 0.1 SDK does not yet define a system-wide file-association registry, so the editor does not claim that association installation is automatic.

## Runtime

Install the free GUI dependency:

```bash
python3 -m pip install --user PyQt6
```

Run without a file:

```bash
python3 app/main.py
```

Open a UTF-8 file:

```bash
python3 app/main.py /path/to/file.txt
```

Headless launch check:

```bash
QT_QPA_PLATFORM=offscreen python3 app/main.py --self-test
```

Recent files are stored under `$SOHD_EDITOR_DATA_DIR/recent.json` when that variable is set. Otherwise the editor uses `$XDG_STATE_HOME/sohd-document-editor/recent.json` or `~/.local/state/sohd-document-editor/recent.json`.

## Keyboard shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+N` | New document |
| `Ctrl+O` | Open |
| `Ctrl+S` | Save |
| `Ctrl+Shift+S` | Save As |
| `Ctrl+H` | Find and replace |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Ctrl+A` | Select all |
| `Ctrl++` | Zoom in |
| `Ctrl+-` | Zoom out |
| `Ctrl+Q` | Quit |

## Sohd packaging

Use the existing Sohd App Format 0.1 SDK:

```bash
cd /home/ubuntu/Sohd-App-Format
./bin/sohd build /home/ubuntu/Sohdow-Apps/Sohd-Document-Editor
./bin/sohd package /home/ubuntu/Sohdow-Apps/Sohd-Document-Editor \
  --output /home/ubuntu/Sohdow-Apps/Sohd-Document-Editor/dist/Sohd-Document-Editor.soh
./bin/sohd validate /home/ubuntu/Sohdow-Apps/Sohd-Document-Editor/dist/Sohd-Document-Editor.soh
./bin/sohd install /home/ubuntu/Sohdow-Apps/Sohd-Document-Editor/dist/Sohd-Document-Editor.soh \
  --root /tmp/sohd-document-editor-install
QT_QPA_PLATFORM=offscreen ./bin/sohd run org.sohdow.documenteditor \
  --root /tmp/sohd-document-editor-install -- --self-test
```

The manifest uses `runtime: "python3"`, the existing Format 0.1 schema, and declarative filesystem read/write permissions. The current SDK does not enforce an OS sandbox.

## Scope and license

This project contains only Sohd Document Editor 0.1. It does not add a new package format, editor engine, cloud sync service, file-association registry, or another application. The project code is MIT licensed. PyQt6 and Qt retain their own licenses as documented in [DEPENDENCIES.md](docs/DEPENDENCIES.md).
