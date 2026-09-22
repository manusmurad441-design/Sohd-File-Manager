# Runtime and packaging

Install the free desktop dependency once on the host:

```bash
python3 -m pip install --user PyQt6
```

Run from source:

```bash
python3 app/main.py
```

For headless validation:

```bash
QT_QPA_PLATFORM=offscreen python3 app/main.py --self-test
```

Build and package using the existing Sohd SDK:

```bash
/home/ubuntu/Sohd-App-Format/bin/sohd build /path/to/Sohd-File-Manager
/home/ubuntu/Sohd-App-Format/bin/sohd package /path/to/Sohd-File-Manager \
  --output /path/to/Sohd-File-Manager/dist/Sohd-File-Manager.soh
/home/ubuntu/Sohd-App-Format/bin/sohd validate /path/to/Sohd-File-Manager/dist/Sohd-File-Manager.soh
```
