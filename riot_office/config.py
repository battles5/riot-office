"""The Riot configuration of LibreOffice, and the per-user interface language.

The configuration is a small set of installation-wide layers, ``config/riot-office*.xcd`` (common
settings plus one file per module), copied into the folder LibreOffice reads such layers from.
It only changes defaults, so every user can still change any setting. The interface language is
a per-user setting, written into the user's ``registrymodifications.xcu`` (LibreOffice must be
closed, as it rewrites that file on exit).
"""

import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from .libreoffice import Installation
from .paths import CONFIG_DIR, libreoffice_user_dir

XCD_GLOB = "riot-office*.xcd"
OOR = "http://openoffice.org/2001/registry"
XS = "http://www.w3.org/2001/XMLSchema"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
LINGUISTIC_PATH = "/org.openoffice.Office.Linguistic/General"

EMPTY_MODIFICATIONS = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    f'<oor:items xmlns:oor="{OOR}" xmlns:xs="{XS}" xmlns:xsi="{XSI}">\n</oor:items>\n'
)


def shipped_files(source: Path = CONFIG_DIR) -> list[Path]:
    """The Riot layers of this version: every ``riot-office*.xcd`` in ``source`` (a folder or one file)."""
    return [source] if source.is_file() else sorted(source.glob(XCD_GLOB))


def installed_files(inst: Installation) -> list[Path]:
    """The Riot layers currently next to LibreOffice's own registry files."""
    return sorted(inst.registry_dir.glob(XCD_GLOB)) if inst.registry_dir.is_dir() else []


def is_installed(inst: Installation) -> bool:
    """True when every Riot layer is in place and identical to the one shipped with this version."""
    shipped = shipped_files()
    return bool(shipped) and all(
        (inst.registry_dir / f.name).exists() and (inst.registry_dir / f.name).read_bytes() == f.read_bytes()
        for f in shipped)


def install(inst: Installation, source: Path = CONFIG_DIR) -> list[Path]:
    """Copy the Riot layers into the installation (needs administrator / root rights).

    When ``source`` is a folder, layers of an older version that it no longer contains are removed.
    ``source`` may also be a single file.
    """
    files = shipped_files(source)
    if not files:
        raise FileNotFoundError(f"no {XCD_GLOB} files in {source}")
    for f in files:
        ET.parse(f)  # never install a broken file: LibreOffice would refuse to start
    inst.registry_dir.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        keep = {f.name for f in files}
        for old in installed_files(inst):
            if old.name not in keep:
                old.unlink()
    written = []
    for f in files:
        target = inst.registry_dir / f.name
        shutil.copyfile(f, target)
        written.append(target)
    return written


def uninstall(inst: Installation) -> bool:
    """Remove every Riot layer; True when there was at least one."""
    found = installed_files(inst)
    for f in found:
        f.unlink()
    return bool(found)


def _modifications_file(user_dir: Path | None) -> Path:
    return (user_dir or libreoffice_user_dir()) / "registrymodifications.xcu"


def get_ui_locale(user_dir: Path | None = None) -> str | None:
    """The interface language set in the user's profile ("it", "en-US"), None when not set."""
    path = _modifications_file(user_dir)
    if not path.exists():
        return None
    for item in ET.parse(path).getroot().iter("item"):
        if item.get(f"{{{OOR}}}path") == LINGUISTIC_PATH:
            prop = item.find("prop")
            if prop is not None and prop.get(f"{{{OOR}}}name") == "UILocale":
                value = prop.find("value")
                return value.text if value is not None else None
    return None


def set_ui_locale(locale: str, user_dir: Path | None = None) -> Path:
    """Set LibreOffice's interface language for the current user, creating the profile file if needed.

    The file is edited as text, one ``<item>`` per line like LibreOffice writes it, so the rest of
    the user's settings are left byte for byte as they were.
    """
    path = _modifications_file(user_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = path.read_text(encoding="utf-8") if path.exists() else EMPTY_MODIFICATIONS
    item = (f'<item oor:path="{LINGUISTIC_PATH}"><prop oor:name="UILocale" oor:op="fuse">'
            f"<value>{locale}</value></prop></item>")
    lines = text.splitlines(keepends=True)
    kept = [line for line in lines if not (f'oor:path="{LINGUISTIC_PATH}"' in line and 'oor:name="UILocale"' in line)]
    out = "".join(kept)
    closing = out.rfind("</oor:items>")
    if closing < 0:
        raise ValueError(f"{path} is not a LibreOffice registrymodifications file")
    out = out[:closing] + item + "\n" + out[closing:]
    ET.fromstring(out.encode("utf-8"))  # still well-formed
    path.write_text(out, encoding="utf-8")
    return path
