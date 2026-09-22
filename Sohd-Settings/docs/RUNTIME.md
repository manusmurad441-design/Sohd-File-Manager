# Runtime and packaging

Install the free GUI dependency on the host:

```bash
python3 -m pip install --user PyQt6
```

Optional host tools improve the Sound and Network sections:

- `pactl` or `wpctl` for audio volume and mute controls;
- `nmcli` or `ip` for network status.

Run from source:

```bash
python3 app/main.py
```

Headless launch check:

```bash
QT_QPA_PLATFORM=offscreen python3 app/main.py --self-test
```

Build and package with the existing SDK:

```bash
/home/ubuntu/Sohd-App-Format/bin/sohd build /path/to/Sohd-Settings
/home/ubuntu/Sohd-App-Format/bin/sohd package /path/to/Sohd-Settings \
  --output /path/to/Sohd-Settings/dist/Sohd-Settings.soh
/home/ubuntu/Sohd-App-Format/bin/sohd validate /path/to/Sohd-Settings/dist/Sohd-Settings.soh
```

The Settings app does not silently fake unavailable host controls. When `pactl`, `wpctl`, or `nmcli` is absent, it reports that the corresponding host integration is unavailable.
