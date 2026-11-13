"""Find LibreOffice, read its version, start its modules and convert files with it headless."""

import configparser
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from .paths import DATA_DIR

MODULES = ("writer", "calc", "impress", "draw")
# Headless conversions run on their own profile, so a LibreOffice window that is already open
# (which would otherwise take over the command and ignore --headless) does not get in the way.
CONVERT_PROFILE = DATA_DIR / "convert-profile"
# PDF export filters per module, and the option that selects PDF/A-2b (SelectPdfVersion = 2).
PDF_FILTERS = {
    "writer": "writer_pdf_Export",
    "calc": "calc_pdf_Export",
    "impress": "impress_pdf_Export",
    "draw": "draw_pdf_Export",
}
PDFA2B = '{"SelectPdfVersion":{"type":"long","value":"2"}}'
EXTENSION_MODULE = {
    **dict.fromkeys(("doc", "docx", "docm", "dotx", "dot", "odt", "ott", "rtf", "txt", "html", "htm", "md"), "writer"),
    **dict.fromkeys(("xls", "xlsx", "xlsm", "xlsb", "xltx", "ods", "ots", "csv", "tsv"), "calc"),
    **dict.fromkeys(("ppt", "pptx", "pptm", "potx", "pps", "ppsx", "odp", "otp"), "impress"),
    **dict.fromkeys(("odg", "otg", "vsd", "vsdx", "pub", "svg"), "draw"),
}


@dataclass(frozen=True)
class Installation:
    """A LibreOffice installation: its ``program`` folder and the soffice executable in it."""

    soffice: Path

    @property
    def program_dir(self) -> Path:
        return self.soffice.parent

    @property
    def console_soffice(self) -> Path:
        """On Windows soffice.com writes to the console (needed for --version and headless runs)."""
        com = self.soffice.with_suffix(".com")
        return com if sys.platform == "win32" and com.exists() else self.soffice

    @property
    def registry_dir(self) -> Path:
        """Where installation-wide configuration layers (*.xcd) are read from."""
        etc = Path("/etc/libreoffice/registry")
        if sys.platform.startswith("linux") and etc.is_dir() and str(self.soffice).startswith("/usr/"):
            return etc  # Debian/Ubuntu packages read this folder (and it survives upgrades).
        return self.program_dir.parent / "share" / "registry"

    def version(self) -> str | None:
        """The version as "26.8.3.2", or None when it cannot be read."""
        for name in ("version.ini", "versionrc"):
            ini = self.program_dir / name
            if ini.exists():
                parser = configparser.ConfigParser(interpolation=None, strict=False)
                try:
                    parser.read_string(ini.read_text(encoding="utf-8", errors="replace"))
                except configparser.Error:
                    continue
                for section in parser.sections():
                    for key in ("msiproductversion", "productversion"):
                        value = parser[section].get(key)
                        if value and re.match(r"\d+\.\d+", value):
                            return value.strip()
        try:
            out = subprocess.run([str(self.console_soffice), "--version"], capture_output=True, text=True,
                                 timeout=60).stdout
        except (OSError, subprocess.SubprocessError):
            return None
        match = re.search(r"(\d+\.\d+\.\d+(?:\.\d+)?)", out)
        return match.group(1) if match else None


def _windows_registry_candidates() -> list[Path]:
    try:
        import winreg
    except ImportError:
        return []
    found = []
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
            try:
                with winreg.OpenKey(hive, r"SOFTWARE\LibreOffice\UNO\InstallPath", 0, winreg.KEY_READ | view) as key:
                    found.append(Path(winreg.QueryValueEx(key, "")[0]) / "soffice.exe")
            except OSError:
                pass
    return found


def candidates() -> list[Path]:
    """Every place where soffice may be, most specific first."""
    paths = []
    if os.environ.get("RIOT_SOFFICE"):
        paths.append(Path(os.environ["RIOT_SOFFICE"]))
    if sys.platform == "win32":
        paths += _windows_registry_candidates()
        for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
            if base:
                paths.append(Path(base) / "LibreOffice" / "program" / "soffice.exe")
    else:
        paths += [Path("/usr/lib/libreoffice/program/soffice"), Path("/usr/lib64/libreoffice/program/soffice")]
        paths += sorted(Path("/opt").glob("libreoffice*/program/soffice"), reverse=True)
    for name in ("soffice", "libreoffice"):
        which = shutil.which(name)
        if which:
            paths.append(Path(which).resolve())
    return paths


def find() -> Installation | None:
    """The LibreOffice installation to use, or None when there is none."""
    for path in candidates():
        if path.is_file():
            # /usr/bin/libreoffice is a wrapper script: prefer the real program folder next to it.
            if path.parent.name != "program":
                real = Path("/usr/lib/libreoffice/program/soffice")
                if real.is_file():
                    path = real
            return Installation(path)
    return None


def launch(inst: Installation, module: str | None = None, files: list[Path] | None = None) -> subprocess.Popen:
    """Open LibreOffice: a module's start page, or the given files with the right module."""
    args = [str(inst.soffice)]
    if module and not files:
        if module not in MODULES:
            raise ValueError(f"unknown module: {module}")
        args.append(f"--{module}")
    args += [str(f) for f in files or []]
    kwargs = {"creationflags": 0x00000008} if sys.platform == "win32" else {"start_new_session": True}  # detached
    return subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kwargs)


def module_for(path: Path) -> str:
    """The LibreOffice module that opens ``path`` (by extension; Writer when unknown)."""
    return EXTENSION_MODULE.get(path.suffix.lower().lstrip("."), "writer")


def convert(inst: Installation, files: list[Path], out_dir: Path, target: str = "pdf", pdfa: bool = False,
            timeout: int = 600) -> list[Path]:
    """Convert ``files`` into ``out_dir`` with LibreOffice headless and return the files written.

    ``target`` is an extension ("pdf", "docx", "xlsx", "pptx", "odt", ...). For PDF the right export
    filter is picked per document type, optionally producing PDF/A-2b.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    CONVERT_PROFILE.mkdir(parents=True, exist_ok=True)
    written = []
    for src in files:
        spec = target
        if target == "pdf":
            spec = f"pdf:{PDF_FILTERS[module_for(src)]}" + (f":{PDFA2B}" if pdfa else "")
        args = [str(inst.console_soffice), f"-env:UserInstallation={CONVERT_PROFILE.as_uri()}", "--headless",
                "--norestore", "--nolockcheck", "--convert-to", spec, "--outdir", str(out_dir), str(src)]
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        dest = out_dir / f"{src.stem}.{target}"
        if result.returncode != 0 or not dest.exists():
            raise RuntimeError(f"conversion of {src.name} failed: {(result.stderr or result.stdout).strip()}")
        written.append(dest)
    return written
