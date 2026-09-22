"""Real local data and host-control services for Sohd Settings 0.1."""

from __future__ import annotations

import json
import locale
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any


def _run(command: list[str], timeout: float = 3.0) -> tuple[bool, str]:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return False, ""
    return result.returncode == 0, result.stdout.strip() or result.stderr.strip()


def settings_path() -> Path:
    root = os.environ.get("SOHD_SETTINGS_DIR")
    if root:
        return Path(root).expanduser().resolve() / "settings.json"
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser()
    return (config_home / "sohd" / "settings.json").resolve()


def load_settings() -> dict[str, Any]:
    try:
        value = json.loads(settings_path().read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}


def save_settings(values: dict[str, Any]) -> Path:
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(values, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)
    return path


def system_information() -> dict[str, str]:
    uname = platform.uname()
    return {
        "Operating system": platform.system() or "Unknown",
        "Release": platform.release() or "Unknown",
        "Version": platform.version() or "Unknown",
        "Kernel machine": uname.machine or "Unknown",
        "Processor": platform.processor() or "Unknown",
        "Python": platform.python_version(),
        "Locale": locale.setlocale(locale.LC_ALL, None),
        "Hostname": platform.node() or "Unknown",
    }


def screen_information(screen) -> dict[str, str]:
    geometry = screen.geometry()
    available = screen.availableGeometry()
    return {
        "Screen": screen.name() or "Primary display",
        "Resolution": f"{geometry.width()} × {geometry.height()}",
        "Available area": f"{available.width()} × {available.height()}",
        "Refresh rate": f"{screen.refreshRate():.2f} Hz",
        "Device pixel ratio": f"{screen.devicePixelRatio():.2f}",
    }


def storage_information(path: str | Path = "/") -> dict[str, int]:
    usage = shutil.disk_usage(Path(path).expanduser().resolve())
    return {"total": usage.total, "used": usage.used, "free": usage.free}


def network_information() -> dict[str, str]:
    ok, output = _run(["nmcli", "-t", "-f", "WIFI,STATE,CONNECTION", "general"])
    if ok and output:
        return {"source": "NetworkManager", "status": output}
    ok, output = _run(["ip", "-brief", "address"])
    if ok and output:
        return {"source": "iproute2", "status": output}
    return {"source": "Unavailable", "status": "No nmcli or ip command is available on this host."}


def audio_information() -> dict[str, str]:
    ok, output = _run(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"])
    if ok and output:
        return {"source": "PipeWire", "status": output}
    ok, output = _run(["pactl", "get-sink-volume", "@DEFAULT_SINK@"]) 
    if ok and output:
        muted_ok, muted = _run(["pactl", "get-sink-mute", "@DEFAULT_SINK@"]) 
        return {"source": "PulseAudio", "status": output + (f"\n{muted}" if muted_ok else "")}
    return {"source": "Unavailable", "status": "No wpctl or pactl command is available on this host."}


def set_audio_mute(muted: bool) -> tuple[bool, str]:
    ok, output = _run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "1" if muted else "0"])
    if ok:
        return True, output or ("Muted" if muted else "Unmuted")
    ok, output = _run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1" if muted else "0"])
    return ok, output or ("Muted" if muted else "Unmuted") if ok else "Audio control unavailable"


def toggle_audio_mute() -> tuple[bool, str]:
    ok, output = _run(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"])
    if ok:
        muted = "MUTED" in output.upper()
        return set_audio_mute(not muted)
    ok, output = _run(["pactl", "get-sink-mute", "@DEFAULT_SINK@"]) 
    if ok:
        muted = "yes" in output.lower()
        return set_audio_mute(not muted)
    return False, "Audio control unavailable"


def set_audio_volume(percent: int) -> tuple[bool, str]:
    value = max(0, min(100, int(percent)))
    ok, output = _run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{value}%"])
    if ok:
        return True, output or f"Volume set to {value}%"
    ok, output = _run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{value}%"])
    return ok, output or f"Volume set to {value}%" if ok else "Audio control unavailable"


def installed_applications(root: str | Path | None = None) -> list[dict[str, str]]:
    install_root = Path(root or os.environ.get("SOHD_HOME", "~/.local/share/sohd")).expanduser().resolve()
    registry_path = install_root / "registry.json"
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        applications = registry.get("applications", {})
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        applications = {}
    if not isinstance(applications, dict):
        return []
    result = []
    for app_id, value in sorted(applications.items()):
        if isinstance(value, dict):
            result.append({"id": str(app_id), "version": str(value.get("version", "unknown")), "root": str(install_root / "apps" / app_id)})
    return result
