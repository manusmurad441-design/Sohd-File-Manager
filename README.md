# Sohd File Manager 0.1

Sohd File Manager is the second official Sohdow application. It is a native desktop file manager built with PyQt6 and Python’s standard library. It works on local HDDs, SSDs, removable volumes mounted by the host system, and ordinary folders without a cloud service or database.

## Features

The application provides a filesystem tree with root, home, and temporary-volume shortcuts; path navigation; sortable files and folders; create folder; rename; copy; cut; paste; permanent delete with confirmation; recursive case-insensitive search; file and folder properties; native opening through desktop associations; storage totals, used space, and free space; `.soh` package manifest inspection; and keyboard shortcuts.

The file manager does not include placeholder buttons. Every toolbar and menu operation invokes a concrete filesystem, Qt model, storage, search, package-inspection, or desktop-open operation.

## Runtime

Install the free open-source GUI binding once:

```bash
python3 -m pip install --user PyQt6
```

See [dependencies and licenses](docs/DEPENDENCIES.md) and [runtime instructions](docs/RUNTIME.md).

Run the application from source:

```bash
cd /home/ubuntu/Sohdow-Apps/Sohd-File-Manager
python3 app/main.py
```

Use `--self-test` for a short launch-and-exit check:

```bash
QT_QPA_PLATFORM=offscreen python3 app/main.py --self-test
```

## Keyboard shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+O` | Open selected file |
| `Ctrl+Shift+N` | Create a folder |
| `F2` | Rename the selected item |
| `Ctrl+C` | Copy selected items |
| `Ctrl+X` | Mark selected items to move |
| `Ctrl+V` | Paste into the current folder |
| `Delete` | Delete selected items after confirmation |
| `Alt+Enter` | Show file properties |
| `Ctrl+F` | Search the current folder recursively |
| `F5` | Refresh the current folder |
| `Alt+Up` | Go to the parent folder |
| `Alt+Left` | Navigate to the parent folder |
| `Alt+Right` | Re-open the path in the address bar |
| `Ctrl+Q` | Quit |

## Sohd packages

`.soh` files are shown as **Sohd application packages**. Double-clicking or opening one reads its `manifest.json` and displays the application name, version, and ID. Invalid or unreadable packages produce an error dialog and are not executed. The file manager does not install packages; installation remains the responsibility of the Sohd SDK and future Sohdow OS policy.

## Building and packaging

Use the existing Sohd App Format 0.1 SDK:

```bash
cd /home/ubuntu/Sohd-App-Format
./bin/sohd build /home/ubuntu/Sohdow-Apps/Sohd-File-Manager
./bin/sohd package /home/ubuntu/Sohdow-Apps/Sohd-File-Manager \
  --output /home/ubuntu/Sohdow-Apps/Sohd-File-Manager/dist/Sohd-File-Manager.soh
./bin/sohd validate /home/ubuntu/Sohdow-Apps/Sohd-File-Manager/dist/Sohd-File-Manager.soh
./bin/sohd install /home/ubuntu/Sohdow-Apps/Sohd-File-Manager/dist/Sohd-File-Manager.soh \
  --root /tmp/sohd-file-manager-install
./bin/sohd run org.sohdow.filemanager --root /tmp/sohd-file-manager-install -- --self-test
```

## Scope

This project contains only Sohd File Manager 0.1. It does not implement Sohd Store, Sohdow OS, package installation, cloud synchronization, network file shares, archive extraction, or another application.

## License

The project code is MIT licensed. PyQt6, Qt, and host desktop utilities retain their own licenses as described in [DEPENDENCIES.md](docs/DEPENDENCIES.md).
