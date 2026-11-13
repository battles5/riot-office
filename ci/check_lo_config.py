"""CI check: does a running LibreOffice actually see the Riot configuration layer?

    python3 ci/check_lo_config.py [soffice]

Starts LibreOffice headless on a throw-away profile, connects through UNO (python3-uno on
Ubuntu, LibreOffice's own python.exe on Windows) and reads back every value that
config/riot-office*.xcd set. Exits non-zero when one of them differs.
"""

import subprocess
import sys
import tempfile
import time
from pathlib import Path

import uno
from com.sun.star.beans import PropertyValue

EXPECTED = {
    ("/org.openoffice.Setup/Office/Factories/com.sun.star.text.TextDocument", "ooSetupFactoryDefaultFilter"): "MS Word 2007 XML",
    ("/org.openoffice.Setup/Office/Factories/com.sun.star.sheet.SpreadsheetDocument", "ooSetupFactoryDefaultFilter"): "Calc MS Excel 2007 XML",
    ("/org.openoffice.Setup/Office/Factories/com.sun.star.presentation.PresentationDocument", "ooSetupFactoryDefaultFilter"): "Impress MS PowerPoint 2007 XML",
    ("/org.openoffice.Office.Common/Save/Document", "WarnAlienFormat"): False,
    ("/org.openoffice.Office.Common/Security/Scripting", "MacroSecurityLevel"): 2,
    ("/org.openoffice.Office.Common/Misc", "CrashReport"): False,
    ("/org.openoffice.Office.Common/Font/Substitution", "Replacement"): True,
    ("/org.openoffice.Office.Common/Font/Substitution/FontPairs/RiotAptos", "SubstituteFont"): "Carlito",
    ("/org.openoffice.Office.UI.ToolbarMode/Applications/Writer", "Active"): "notebookbar.ui",
    ("/org.openoffice.Office.UI.ToolbarMode/Applications/Calc", "Active"): "notebookbar.ui",
    ("/org.openoffice.Office.UI.ToolbarMode/Applications/Impress", "Active"): "notebookbar.ui",
}


def read(provider, path: str, name: str):
    arg = PropertyValue()
    arg.Name, arg.Value = "nodepath", path
    node = provider.createInstanceWithArguments("com.sun.star.configuration.ConfigurationAccess", (arg,))
    return node.getPropertyValue(name)


def main() -> int:
    soffice = sys.argv[1] if len(sys.argv) > 1 else "soffice"
    with tempfile.TemporaryDirectory() as profile:
        proc = subprocess.Popen([soffice, f"-env:UserInstallation={Path(profile).as_uri()}", "--headless", "--norestore",
                                 "--nologo", "--accept=socket,host=127.0.0.1,port=2083;urp;"])
        try:
            local = uno.getComponentContext()
            resolver = local.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local)
            for _ in range(120):
                try:
                    ctx = resolver.resolve("uno:socket,host=127.0.0.1,port=2083;urp;StarOffice.ComponentContext")
                    break
                except Exception:
                    time.sleep(1)
            else:
                print("could not connect to LibreOffice")
                return 1
            provider = ctx.ServiceManager.createInstanceWithContext("com.sun.star.configuration.ConfigurationProvider", ctx)
            failures = 0
            for (path, name), expected in EXPECTED.items():
                try:
                    value = read(provider, path, name)
                except Exception as exc:
                    value = f"<error {exc}>"
                ok = value == expected
                failures += not ok
                print(f"[{'ok' if ok else 'FAIL'}] {path}/{name} = {value!r} (expected {expected!r})")
            try:
                desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
                desktop.terminate()
            except Exception:
                pass
            return 1 if failures else 0
        finally:
            try:
                proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == "__main__":
    sys.exit(main())
