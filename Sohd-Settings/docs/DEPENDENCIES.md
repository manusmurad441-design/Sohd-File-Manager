# Sohd Settings 0.1 dependencies and licenses

Sohd Settings is a local native desktop application. It uses PyQt6 for widgets and Python’s standard library for local settings persistence, operating-system information, storage statistics, locale detection, and subprocess calls to optional host tools.

| Component | Use | License / notice |
|---|---|---|
| Python 3.11+ | Application runtime and standard library | Python Software Foundation License; https://docs.python.org/3/license.html |
| PyQt6 | Native desktop widgets, dialogs, screen information, and application palette | GPLv3 or commercial license; this project uses it under GPLv3-compatible open-source terms. Source: https://www.riverbankcomputing.com/software/pyqt/ |
| Qt 6 | Desktop UI toolkit and platform integration | LGPLv3/GPLv3/commercial options depending on module; https://www.qt.io/licensing/ |
| `pactl` / `wpctl` | Optional real host audio volume and mute controls | Host-provided PulseAudio/PipeWire command-line tools; no service or API is bundled. |
| `nmcli` / `ip` | Optional real host network status information | Host-provided NetworkManager / iproute2 tools; no network service is bundled. |
| `sohd` | Optional local management of installed Sohd applications | Existing local Sohd SDK only; no store or cloud service is used. |

The `.soh` package does not bundle PyQt6 or host utilities. It declares requested capabilities in `manifest.json`, but current Sohd App Format 0.1 treats permissions as declarative metadata and does not enforce them at runtime.

The project code is MIT licensed. Third-party runtime components retain their own licenses.
