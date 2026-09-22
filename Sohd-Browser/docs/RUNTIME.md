# Runtime requirements

Sohd Browser 0.1 is a real Qt WebEngine desktop application. Install the free open-source runtime with:

```bash
python3 -m pip install --user PyQt6 PyQt6-WebEngine
```

The package itself is built with the existing local Sohd SDK and remains a normal `.soh` archive. The SDK package format does not install Python dependencies automatically. This is intentional: the host or future Sohdow runtime should select and manage approved system components.

For a headless smoke test in development environments:

```bash
QT_QPA_PLATFORM=offscreen \
QTWEBENGINE_CHROMIUM_FLAGS="--no-sandbox --disable-gpu" \
./bin/sohd run org.sohdow.browser --root ./local-sohd
```

A regular desktop session should omit `QT_QPA_PLATFORM=offscreen` and allow Qt to use the user’s display server.
