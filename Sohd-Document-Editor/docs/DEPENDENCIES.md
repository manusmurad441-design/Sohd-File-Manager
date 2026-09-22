# Sohd Document Editor 0.1 dependencies and licenses

Sohd Document Editor uses PyQt6 for native widgets and Python’s standard library for UTF-8 file I/O, recent-file persistence, and command-line path handling. Syntax highlighting is implemented locally with Qt’s `QSyntaxHighlighter`; no editor engine, cloud service, or paid API is required.

| Component | Use | License / notice |
|---|---|---|
| Python 3.11+ | Runtime, UTF-8 I/O, JSON recent-file state | Python Software Foundation License; https://docs.python.org/3/license.html |
| PyQt6 | Native text editor widgets, dialogs, menus, and syntax-highlighter base class | GPLv3 or commercial license; this project uses it under GPLv3-compatible open-source terms. Source: https://www.riverbankcomputing.com/software/pyqt/ |
| Qt 6 | Desktop UI toolkit and rich text editing primitives | LGPLv3/GPLv3/commercial options depending on module; https://www.qt.io/licensing/ |

The package does not bundle PyQt6 or Qt binaries. The host provides the compatible runtime. The application code is MIT licensed, while PyQt6 and Qt retain their own licenses.
