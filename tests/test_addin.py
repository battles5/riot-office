"""Tests of the Calc add-in package and of the ``addin`` command (no LibreOffice needed)."""

import re
import stat
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import pytest

from riot_office import addin, libreoffice

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "addins" / "calc" / "extension"))
sys.path.insert(0, str(ROOT / "addins" / "calc"))

import build_oxt  # noqa: E402
import riot_calc_meta as meta  # noqa: E402

IDL = (ROOT / "addins" / "calc" / "idl" / "XRiotFunctions.idl").read_text(encoding="utf-8")


def idl_methods() -> dict[str, list[str]]:
    """Method name -> parameter names, read from the IDL."""
    found = {}
    for match in re.finditer(r"(?:any|double|sequence<\s*sequence<\s*any\s*>\s*>)\s+(\w+)\s*\((.*?)\)\s*;", IDL, re.S):
        found[match.group(1)] = re.findall(r"\]\s*(?:sequence<[^;]*?>|\w+)\s+(\w+)\s*[,)]", match.group(2) + ")")
    return found


def test_meta_matches_the_idl():
    methods = idl_methods()
    assert set(methods) == set(meta.FUNCTIONS)
    for name, data in meta.FUNCTIONS.items():
        assert [arg for arg, _ in data["args"]] == methods[name], name
        assert data["display"] == name.upper()
        for _, texts in data["args"]:
            assert set(texts) == {"en", "it"}
        assert set(data["description"]) == {"en", "it"}


def test_type_library_is_committed():
    assert (ROOT / "addins" / "calc" / "types" / "RiotFunctions.rdb").stat().st_size > 100


def test_oxt_contents(tmp_path):
    oxt = build_oxt.build_oxt(tmp_path)
    with zipfile.ZipFile(oxt) as z:
        names = set(z.namelist())
        assert {"META-INF/manifest.xml", "description.xml", "CalcAddIns.xcu", "riot_calc_functions.py",
                "riot_calc_meta.py", "excel_functions.py", "RiotFunctions.rdb"} <= names
        for xml in ("META-INF/manifest.xml", "description.xml", "CalcAddIns.xcu"):
            ET.fromstring(z.read(xml))
        manifest = z.read("META-INF/manifest.xml").decode()
        for entry in ("RiotFunctions.rdb", "riot_calc_functions.py", "CalcAddIns.xcu"):
            assert f'full-path="{entry}"' in manifest
        # The logic bundled in the extension is the very module that the unit tests exercise.
        assert z.read("excel_functions.py") == (ROOT / "riot_office" / "excel_functions.py").read_bytes()
        xcu = ET.fromstring(z.read("CalcAddIns.xcu"))
    oor = "{http://openoffice.org/2001/registry}name"
    functions = {n.get(oor): n for n in xcu.iter("node") if n.get(oor) in meta.FUNCTIONS}
    assert set(functions) == set(meta.FUNCTIONS)
    for name, node in functions.items():
        params = [n.get(oor) for n in node.find("node").iter("node") if n.get(oor) in dict(meta.FUNCTIONS[name]["args"])]
        assert params == [arg for arg, _ in meta.FUNCTIONS[name]["args"]]


def test_shim_declares_every_idl_method():
    source = (ROOT / "addins" / "calc" / "extension" / "riot_calc_functions.py").read_text(encoding="utf-8")
    for name in idl_methods():
        assert f"def {name}(self" in source
    # Calc ignores an add-in that does not implement XServiceName.
    assert "XServiceName" in source and "def getServiceName" in source


@pytest.mark.skipif(sys.platform == "win32", reason="uses a shell script as the fake unopkg")
def test_install_and_uninstall_call_unopkg(tmp_path):
    program = tmp_path / "program"
    program.mkdir()
    (program / "soffice").write_text("")
    log = tmp_path / "calls.log"
    fake = program / "unopkg"
    fake.write_text(f'#!/bin/sh\necho "$@" >> {log}\n'
                    f'if [ "$1" = list ]; then echo "Identifier: {addin.IDENTIFIER}"; fi\n')
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    inst = libreoffice.Installation(program / "soffice")
    oxt = tmp_path / "x.oxt"
    oxt.write_text("x")

    assert addin.install(inst, oxt=oxt) == oxt
    assert addin.is_installed(inst)
    assert addin.uninstall(inst)
    calls = log.read_text().splitlines()
    assert calls[0] == f"add --shared --suppress-license {oxt}"
    assert calls[1] == "list --shared"
    assert calls[-1] == f"remove --shared {addin.IDENTIFIER}"

    addin.install(inst, user=True, oxt=oxt)
    assert "--shared" not in log.read_text().splitlines()[-1]


@pytest.mark.skipif(sys.platform == "win32", reason="uses a shell script as the fake unopkg")
def test_install_reports_unopkg_errors(tmp_path):
    program = tmp_path / "program"
    program.mkdir()
    (program / "soffice").write_text("")
    fake = program / "unopkg"
    fake.write_text("#!/bin/sh\necho 'ERROR: not allowed' >&2\nexit 1\n")
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    with pytest.raises(RuntimeError, match="not allowed"):
        addin.install(libreoffice.Installation(program / "soffice"), oxt=tmp_path / "x.oxt")


def test_unopkg_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        addin.unopkg(libreoffice.Installation(tmp_path / "soffice"))


def test_build_script_runs_from_the_command_line(tmp_path):
    result = subprocess.run([sys.executable, str(ROOT / "addins" / "calc" / "build_oxt.py"), "--out", str(tmp_path)],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert list(tmp_path.glob("RiotOffice-ExcelFunctions-*.oxt"))
