"""Install, remove and check the Riot Calc add-in (Excel functions) with LibreOffice's ``unopkg``.

The add-in is an extension, ``RiotOffice-ExcelFunctions-<version>.oxt``. Installers ship it ready
made in ``addins/``; from a source checkout it is built on the fly. It is installed *shared*
(for every user of the PC, needs administrator / root rights) unless ``user=True``.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

from .libreoffice import Installation
from .paths import ROOT

IDENTIFIER = "org.riotoffice.excel-functions"


def unopkg(inst: Installation) -> Path:
    """The ``unopkg`` tool that sits next to ``soffice``."""
    names = ("unopkg.com", "unopkg.exe") if sys.platform == "win32" else ("unopkg",)
    for name in names:
        candidate = inst.soffice.with_name(name)
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"unopkg not found next to {inst.soffice}")


def find_oxt(build_dir: Path | None = None) -> Path:
    """The extension file: a prebuilt one shipped in ``addins/``, otherwise built from the sources."""
    shipped = sorted((ROOT / "addins").glob("RiotOffice-ExcelFunctions-*.oxt"))
    if shipped:
        return shipped[-1]
    builder = ROOT / "addins" / "calc" / "build_oxt.py"
    if not builder.exists():
        raise FileNotFoundError("no extension file and no sources to build it from")
    out = build_dir or Path(tempfile.mkdtemp(prefix="riot-oxt-"))
    subprocess.run([sys.executable, str(builder), "--out", str(out)], check=True, capture_output=True)
    return next(out.glob("*.oxt"))


def _run(inst: Installation, *args: str, user: bool = False) -> subprocess.CompletedProcess:
    command = [str(unopkg(inst)), *args]
    if not user:
        command.insert(2, "--shared")
    return subprocess.run(command, capture_output=True, text=True, timeout=600)


def install(inst: Installation, user: bool = False, oxt: Path | None = None) -> Path:
    """Install (or update) the extension; raises RuntimeError with unopkg's message on failure."""
    oxt = oxt or find_oxt()
    result = _run(inst, "add", "--suppress-license", str(oxt), user=user)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout).strip() or f"unopkg exited with {result.returncode}")
    return oxt


def uninstall(inst: Installation, user: bool = False) -> bool:
    """Remove the extension; False when it was not installed."""
    if not is_installed(inst, user):
        return False
    result = _run(inst, "remove", IDENTIFIER, user=user)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout).strip())
    return True


def is_installed(inst: Installation, user: bool = False) -> bool:
    result = _run(inst, "list", user=user)
    return result.returncode == 0 and IDENTIFIER in result.stdout


def is_available(inst: Installation) -> bool:
    """True when the extension is installed for every user or for the current one."""
    return is_installed(inst) or is_installed(inst, user=True)
