# Sohd File Manager 0.1 dependencies and licenses

Sohd File Manager uses PyQt6 for its desktop widgets and QFileSystemModel. Filesystem operations, search, properties, storage statistics, `.soh` inspection, and launching files use Python’s standard library and the host desktop’s `xdg-open` command. No paid API, cloud service, database, account, or subscription is required.

| Component | Use | License / notice |
|---|---|---|
| Python 3.11+ | Runtime, filesystem operations, ZIP inspection, storage statistics | Python Software Foundation License; https://docs.python.org/3/license.html |
| PyQt6 | Qt desktop widgets, file-system model, dialogs, keyboard actions | GPLv3 or commercial license; this project uses it under GPLv3-compatible open-source terms. Source: https://www.riverbankcomputing.com/software/pyqt/ |
| Qt 6 | Native desktop controls and model/view UI | LGPLv3/GPLv3/commercial options depending on module; https://www.qt.io/licensing/ |
| `xdg-open` | Opens a selected file using the user’s desktop association | Part of common free desktop environments; no service or API is used. |

The `.soh` package does not bundle PyQt6 or Qt binaries. A compatible host runtime must provide PyQt6. This keeps the application package lightweight and avoids redistributing third-party binaries under separate obligations.

The project code is MIT licensed. Runtime dependencies retain their own licenses.
