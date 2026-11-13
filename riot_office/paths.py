"""Where Riot Office keeps its files: program resources, per-user data and LibreOffice's profile."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
DOCS = ROOT / "docs"
CONFIG_DIR = ROOT / "config"
ICON_PNG = ASSETS / "icon.png"
ICON_ICO = ASSETS / "icon.ico"
GUIDE = DOCS / "Guide.html"


def _data_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
        return base / "Riot Office"
    base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return base / "riot-office"


DATA_DIR = _data_dir()


def libreoffice_user_dir() -> Path:
    """The ``user`` folder of LibreOffice's default profile (major profile version 4)."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
        return base / "LibreOffice" / "4" / "user"
    base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "libreoffice" / "4" / "user"
