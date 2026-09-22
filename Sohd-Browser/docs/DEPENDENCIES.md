# Sohd Browser 0.1 dependencies and licenses

Sohd Browser uses a free, locally installed Qt WebEngine runtime. It does not call a paid API, require a subscription, use cloud infrastructure, or send telemetry to a project-controlled service.

| Component | Use | License / notice |
|---|---|---|
| Python 3.11+ | Application runtime and standard library | Python Software Foundation License; https://docs.python.org/3/license.html |
| PyQt6 | Python bindings for Qt 6 widgets and application services | GPLv3 or commercial license; this project uses it under GPLv3-compatible open-source terms. The binding source is available at https://www.riverbankcomputing.com/software/pyqt/ |
| PyQt6-WebEngine | Python bindings for Qt WebEngine | GPLv3 or commercial license; https://www.riverbankcomputing.com/software/pyqtwebengine/ |
| Qt 6 | Desktop widgets and event loop used by PyQt6 | LGPLv3/GPLv3/commercial options depending on module; https://www.qt.io/licensing/ |
| Qt WebEngine | Embedded Chromium-based web rendering, networking, downloads, cookies, and security policies | LGPLv3/GPLv3/commercial options depending on build; https://doc.qt.io/qt-6/qtwebengine-index.html |
| Chromium components | HTML/CSS/JavaScript rendering engine shipped inside Qt WebEngine | Chromium open-source project licenses, principally BSD-style with third-party notices; https://chromium.googlesource.com/chromium/src/+/main/LICENSE |
| DuckDuckGo | Default search URL when a user enters search text | Public web endpoint; no API key is used. Users may change the search URL in a future preference screen. |

The package does not redistribute PyQt6, Qt, Qt WebEngine, or Chromium binaries. The host system must provide a compatible PyQt6 + PyQt6-WebEngine installation. This keeps the `.soh` package small and avoids bundling a large browser engine under separate redistribution obligations.

The application uses only the browser’s ordinary network requests. It has no analytics, remote update channel, account system, store integration, or proprietary source copied into this project.
