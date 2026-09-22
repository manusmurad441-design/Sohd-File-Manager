# Sohd Browser 0.1

Sohd Browser is the first official application in the Sohdow ecosystem. It is a real desktop browser built around Qt WebEngine, with a small Qt interface and local JSON-backed profile state. The project is separate from Sohdow OS and Sohd Store.

## Features

The application provides an address bar with URL normalization and DuckDuckGo search fallback, real web navigation through Chromium-based Qt WebEngine, tab creation and closing, back/forward/reload/home controls, persistent bookmarks, bounded history, download handling with a save dialog, a downloads library, keyboard shortcuts, HTTPS security labels, certificate rejection, error pages, JavaScript enable/disable, cookie and cache clearing, and local profile storage.

There are no placeholder controls. Browser actions are connected to Qt WebEngine or to a concrete local state operation.

## Runtime

Install the free runtime components once on the host:

```bash
python3 -m pip install --user PyQt6 PyQt6-WebEngine
```

See [the dependency and license record](docs/DEPENDENCIES.md) and [runtime notes](docs/RUNTIME.md). The `.soh` package does not bundle the large Qt or Chromium binaries. This keeps distribution lightweight and avoids copying third-party binaries into the application package.

## Run from the source project

```bash
cd Sohdow-Apps/Sohd-Browser
python3 app/main.py
```

Use `--self-test` for a short launch-and-close smoke check:

```bash
python3 app/main.py --self-test
```

Useful shortcuts:

| Shortcut | Action |
|---|---|
| `Ctrl+L` | Focus the address bar |
| `Ctrl+T` | Open a new tab |
| `Ctrl+W` | Close the current tab |
| `Ctrl+R` | Reload the current page |
| `Alt+Left` / `Alt+Right` | Navigate back or forward |
| `Ctrl+D` | Add or remove the current page bookmark |
| `Ctrl+H` | Open history |
| `Ctrl+Shift+B` | Open bookmarks |
| `Ctrl+Q` | Quit |

The address bar also accepts `sohd://home`. Entering a domain without a scheme uses HTTPS. Other text is sent to DuckDuckGo as a search query.

## Local profile data

The profile directory defaults to the Qt application-data location, normally under `~/.local/share/Sohd Browser/`. Set `SOHD_BROWSER_DATA_DIR` to use a test or portable directory. The profile stores only local bookmarks, history, download records, cookies, and cache data. There is no telemetry endpoint.

## Sohd package workflow

From the Sohd SDK project, build and package the browser:

```bash
cd /home/ubuntu/Sohd-App-Format
./bin/sohd build /home/ubuntu/Sohdow-Apps/Sohd-Browser
./bin/sohd package /home/ubuntu/Sohdow-Apps/Sohd-Browser \
  --output /home/ubuntu/Sohdow-Apps/Sohd-Browser/dist/Sohd-Browser.soh
./bin/sohd validate /home/ubuntu/Sohdow-Apps/Sohd-Browser/dist/Sohd-Browser.soh
```

Install and launch it locally:

```bash
./bin/sohd install /home/ubuntu/Sohdow-Apps/Sohd-Browser/dist/Sohd-Browser.soh \
  --root /tmp/sohd-browser-install
./bin/sohd run org.sohdow.browser --root /tmp/sohd-browser-install
```

The manifest declares the local capabilities that a future Sohdow runtime can enforce: `network.access`, `filesystem.downloads`, and `storage.cookies`.

## Architecture

`app/main.py` contains the Qt desktop shell, tab management, WebEngine integration, downloads, dialogs, privacy actions, and error pages. `app/browser_core.py` contains URL normalization, security labels, and JSON-backed bookmark/history/download state so these behaviors can be tested independently of a display server. `docs/` records external runtime licenses and packaging constraints.

## Scope boundary

This project builds only Sohd Browser 0.1. It does not implement Sohd Store, Sohdow OS, a browser synchronization service, an account service, a proprietary search API, or an automatic update service.

## License

The project code is MIT licensed. Runtime components remain under their own licenses; see [DEPENDENCIES.md](docs/DEPENDENCIES.md).
