"""Per-user data directory and JSON save helpers.

All save/run-tracking data goes through this module so nothing is written
next to the executable (which is temporary/read-only in PyInstaller builds).
Don't build paths to the data directory anywhere else.

    Windows  %APPDATA%\\RestenRinger2\\
    Linux    $XDG_DATA_HOME/RestenRinger2/  (default ~/.local/share/RestenRinger2/)
    macOS    ~/Library/Application Support/RestenRinger2/
"""
import json
import os
import platform
from pathlib import Path

APP_NAME = "RestenRinger2"


def _base_data_dir() -> Path:
    system = platform.system()
    home = Path.home()
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        return Path(appdata) if appdata else home / "AppData" / "Roaming"
    if system == "Darwin":
        return home / "Library" / "Application Support"
    xdg = os.environ.get("XDG_DATA_HOME")
    return Path(xdg) if xdg else home / ".local" / "share"


def user_data_dir() -> Path:
    """Return the game's per-user data directory, creating it if needed."""
    path = _base_data_dir() / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def data_path(filename: str) -> Path:
    """Return the full path for a file inside the user data directory."""
    return user_data_dir() / filename


def load_json(filename: str, default=None):
    """Load a JSON file from the data directory.

    Returns `default` if the file is missing or unreadable/corrupt, so a bad
    save never crashes the game.
    """
    path = data_path(filename)
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def save_json(filename: str, data) -> Path:
    """Write `data` as JSON to the data directory.

    Writes to a temp file first and then swaps it in, so a crash mid-write
    doesn't leave a half-written save.
    """
    path = data_path(filename)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)
    return path
