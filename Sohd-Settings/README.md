# Sohd Settings 0.1

Sohd Settings is the third official application in the Sohdow ecosystem. It is a native PyQt6 desktop application for local system information and settings. It does not build Sohdow OS, Sohd Store, a cloud control plane, or a privileged system daemon.

## Sections

- **Appearance:** applies and persists a System, Light, or Dark palette for this Settings application and persists a UI font scale.
- **Display:** reads the active Qt screen name, resolution, available geometry, refresh rate, and device pixel ratio.
- **Sound:** reads the default audio sink and changes volume or mute state through `wpctl` or `pactl` when the host provides one of those tools. If neither is present, the app reports that audio control is unavailable.
- **Network:** reads host status through `nmcli` or `ip` when available. It does not pretend to configure a connection when no supported host tool is present.
- **Storage:** reads real root-filesystem capacity, used space, free space, and percentage.
- **System information:** reads operating system, kernel, architecture, processor, Python, locale, and hostname values.
- **Application management:** lists the local Sohd registry and launches or uninstalls selected installed applications through the existing `sohd` SDK.
- **Language:** persists an English or Arabic language preference. The 0.1 resource set is English; Arabic preference is stored for future localized resources and is reported honestly.
- **About Sohdow:** shows application identity, runtime, scope, and opens the local project license.

Every visible action is connected to a real local operation, Qt platform query, or explicit unavailable-integration result. No fake settings are presented as applied system settings.

## Runtime

Install the free GUI binding:

```bash
python3 -m pip install --user PyQt6
```

Optional host integrations are `wpctl` or `pactl` for audio and `nmcli` or `ip` for network status. See [dependency and license details](docs/DEPENDENCIES.md) and [runtime notes](docs/RUNTIME.md).

Run from source:

```bash
cd /home/ubuntu/Sohdow-Apps/Sohd-Settings
python3 app/main.py
```

Headless smoke check:

```bash
QT_QPA_PLATFORM=offscreen python3 app/main.py --self-test
```

The app stores its local preference file under `$SOHD_SETTINGS_DIR/settings.json` when that variable is set. Otherwise it uses `$XDG_CONFIG_HOME/sohd/settings.json` or `~/.config/sohd/settings.json`.

## Sohd lifecycle

Use the existing Sohd App Format 0.1 SDK:

```bash
cd /home/ubuntu/Sohd-App-Format
./bin/sohd build /home/ubuntu/Sohdow-Apps/Sohd-Settings
./bin/sohd package /home/ubuntu/Sohdow-Apps/Sohd-Settings \
  --output /home/ubuntu/Sohdow-Apps/Sohd-Settings/dist/Sohd-Settings.soh
./bin/sohd validate /home/ubuntu/Sohdow-Apps/Sohd-Settings/dist/Sohd-Settings.soh
./bin/sohd install /home/ubuntu/Sohdow-Apps/Sohd-Settings/dist/Sohd-Settings.soh \
  --root /tmp/sohd-settings-install
QT_QPA_PLATFORM=offscreen ./bin/sohd run org.sohdow.settings \
  --root /tmp/sohd-settings-install -- --self-test
```

The manifest uses `runtime: "python3"` and the existing Sohd App Format 0.1 fields. Its permissions are declarative metadata under the current SDK; the SDK does not yet enforce an OS sandbox.

## Scope and license

This project contains only Sohd Settings 0.1. It does not implement a new package format, OS settings daemon, Store, network account service, or another application. Project code is MIT licensed. PyQt6, Qt, and optional host utilities retain their own licenses as documented in [DEPENDENCIES.md](docs/DEPENDENCIES.md).
