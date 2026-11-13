"""Build the Calc add-in extension: dist/RiotOffice-ExcelFunctions-<version>.oxt

    python addins/calc/build_oxt.py            package the extension
    python addins/calc/build_oxt.py --types    first rebuild types/RiotFunctions.rdb from the IDL

The type library is compiled from idl/XRiotFunctions.idl and committed, because compiling needs
the LibreOffice SDK; rebuild it (``--types --sdk <LibreOffice install dir>``) only when the IDL
changes. The extension is a ZIP holding the Python component, the logic module copied from
``riot_office/excel_functions.py`` (the single source of truth), the type library and a
CalcAddIns.xcu generated from ``extension/riot_calc_meta.py``.
"""

import argparse
import os
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE / "extension"))
sys.path.insert(0, str(ROOT))

import riot_calc_meta as meta  # noqa: E402
from riot_office import __version__  # noqa: E402

IMPLEMENTATION = "org.riotoffice.calc.RiotFunctions"
IDENTIFIER = "org.riotoffice.excel-functions"
LANGUAGES = ("en", "it")
RDB = HERE / "types" / "RiotFunctions.rdb"

MANIFEST = """<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest xmlns:manifest="http://openoffice.org/2001/manifest">
  <manifest:file-entry manifest:full-path="RiotFunctions.rdb" manifest:media-type="application/vnd.sun.star.uno-typelibrary;type=RDB"/>
  <manifest:file-entry manifest:full-path="riot_calc_functions.py" manifest:media-type="application/vnd.sun.star.uno-component;type=Python"/>
  <manifest:file-entry manifest:full-path="CalcAddIns.xcu" manifest:media-type="application/vnd.sun.star.configuration-data"/>
</manifest:manifest>
"""

DESCRIPTION = """<?xml version="1.0" encoding="UTF-8"?>
<description xmlns="http://openoffice.org/extensions/description/2006"
             xmlns:xlink="http://www.w3.org/1999/xlink"
             xmlns:d="http://openoffice.org/extensions/description/2006">
  <identifier value="{identifier}"/>
  <version value="{version}"/>
  <display-name>
    <name lang="en">Riot Office: Excel functions</name>
    <name lang="it">Riot Office: funzioni Excel</name>
  </display-name>
  <publisher>
    <name lang="en" xlink:href="https://github.com/battles5/riot-office">Riot Office</name>
  </publisher>
  <dependencies>
    <OpenOffice.org-minimal-version value="4.0" d:name="LibreOffice 4.0"/>
  </dependencies>
</description>
"""


def values(texts: dict[str, str]) -> str:
    return "".join(f'<value xml:lang="{lang}">{escape(texts[lang])}</value>' for lang in LANGUAGES)


def calc_addins_xcu() -> str:
    """CalcAddIns.xcu: display names, descriptions and argument texts in every language."""
    functions = []
    for programmatic, data in meta.FUNCTIONS.items():
        params = "".join(f"""
          <node oor:name="{name}" oor:op="replace">
            <prop oor:name="DisplayName" oor:type="xs:string">{values(dict.fromkeys(LANGUAGES, meta.snake(name)))}</prop>
            <prop oor:name="Description" oor:type="xs:string">{values(texts)}</prop>
          </node>""" for name, texts in data["args"])
        functions.append(f"""
        <node oor:name="{programmatic}" oor:op="replace">
          <prop oor:name="DisplayName" oor:type="xs:string">{values(dict.fromkeys(LANGUAGES, data["display"]))}</prop>
          <prop oor:name="Description" oor:type="xs:string">{values(data["description"])}</prop>
          <prop oor:name="Category" oor:type="xs:string"><value>{meta.CATEGORY}</value></prop>
          <node oor:name="Parameters">{params}
          </node>
        </node>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<oor:component-data xmlns:oor="http://openoffice.org/2001/registry" xmlns:xs="http://www.w3.org/2001/XMLSchema"
    oor:name="CalcAddIns" oor:package="org.openoffice.Office">
  <node oor:name="AddInInfo">
    <node oor:name="{IMPLEMENTATION}" oor:op="replace">
      <node oor:name="AddInFunctions">{"".join(functions)}
      </node>
    </node>
  </node>
</oor:component-data>
"""


def build_types(sdk: Path) -> None:
    """Compile idl/XRiotFunctions.idl into types/RiotFunctions.rdb with the SDK's unoidl-write."""
    program = sdk / "program"
    tool = sdk / "sdk" / "bin" / "unoidl-write"
    env = {**os.environ, "LD_LIBRARY_PATH": str(program)}
    subprocess.run([str(tool), str(program / "types.rdb"), str(program / "types" / "offapi.rdb"),
                    str(HERE / "idl" / "XRiotFunctions.idl"), str(RDB)], check=True, env=env)
    print("type library:", RDB)


def build_oxt(out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"RiotOffice-ExcelFunctions-{__version__}.oxt"
    files = {
        "META-INF/manifest.xml": MANIFEST,
        "description.xml": DESCRIPTION.format(identifier=IDENTIFIER, version=__version__),
        "CalcAddIns.xcu": calc_addins_xcu(),
        "riot_calc_functions.py": (HERE / "extension" / "riot_calc_functions.py").read_text(encoding="utf-8"),
        "riot_calc_meta.py": (HERE / "extension" / "riot_calc_meta.py").read_text(encoding="utf-8"),
        "excel_functions.py": (ROOT / "riot_office" / "excel_functions.py").read_text(encoding="utf-8"),
        "LICENSE.txt": (ROOT / "LICENSE.txt").read_text(encoding="utf-8"),
    }
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for name, text in files.items():
            z.writestr(name, text)
        z.write(RDB, "RiotFunctions.rdb")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--types", action="store_true", help="rebuild the type library from the IDL first")
    parser.add_argument("--sdk", type=Path, help="LibreOffice install dir that contains program/ and sdk/ (for --types)")
    parser.add_argument("--out", type=Path, default=ROOT / "dist", help="output folder (default: dist)")
    args = parser.parse_args()
    if args.types:
        if not args.sdk:
            parser.error("--types needs --sdk <LibreOffice install dir>")
        build_types(args.sdk)
    print(build_oxt(args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
