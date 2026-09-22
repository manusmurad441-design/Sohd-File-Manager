# Runtime and packaging

Install the free GUI dependency:

```bash
python3 -m pip install --user PyQt6
```

Run the editor without a document:

```bash
python3 app/main.py
```

Open a document from the command line or a desktop file association:

```bash
python3 app/main.py /path/to/document.txt
```

The editor accepts one or more paths after `--`; the first path opens in the current window and later paths open in additional windows:

```bash
python3 app/main.py -- /path/one.txt /path/two.py
```

Headless launch check:

```bash
QT_QPA_PLATFORM=offscreen python3 app/main.py --self-test
```

Build and package using the existing Sohd SDK:

```bash
/home/ubuntu/Sohd-App-Format/bin/sohd build /path/to/Sohd-Document-Editor
/home/ubuntu/Sohd-App-Format/bin/sohd package /path/to/Sohd-Document-Editor \
  --output /path/to/Sohd-Document-Editor/dist/Sohd-Document-Editor.soh
/home/ubuntu/Sohd-App-Format/bin/sohd validate /path/to/Sohd-Document-Editor/dist/Sohd-Document-Editor.soh
```

The current Sohd App Format 0.1 runtime passes command-line arguments to `app/main.py`. This is the integration path for a future Sohdow File Manager association; the current SDK does not yet define a system-wide file-association registry.
