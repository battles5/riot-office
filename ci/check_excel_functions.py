"""CI check: install the Calc add-in into a real LibreOffice and let it calculate a spreadsheet.

    python3 ci/check_excel_functions.py <soffice> [work dir]

Builds the .oxt, installs it into a throw-away profile with unopkg, writes a flat ODF
spreadsheet whose formulas call GROUPBY, PIVOTBY, PERCENTOF and the REGEX functions, converts it
to CSV with LibreOffice and compares the cells. No UNO bridge is needed.

ODF stores an add-in function under its full internal name (<implementation>.<method>), so that
is how the formulas are written here. Typing the short name (=GROUPBY(...)) in Calc goes through a
different lookup, which this check cannot exercise headless. Exits non-zero on any difference.
"""

import csv
import io
import subprocess
import sys
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

ROOT = Path(__file__).resolve().parent.parent
PREFIX = "ORG.RIOTOFFICE.CALC.RIOTFUNCTIONS."

DATA = [["Region", "Product", "Sales"], ["North", "A", 10], ["South", "B", 20], ["north", "B", 5],
        ["West", "A", 7], ["South", "A", 1]]
# name: (top-left cell as (row, column), formula, height, width, expected rows)
CASES = {
    "groupby": ((1, 5), 'GROUPBY([.A1:.A6];[.C1:.C6];"SUM")', 5, 2,
                [["Region", "Sum of Sales"], ["North", "15"], ["South", "21"], ["West", "7"], ["Total", "43"]]),
    "groupby options": ((8, 5), 'GROUPBY([.A2:.A6];[.C2:.C6];"SUM,COUNT";0;-1;-2)', 4, 3,
                        [["Total", "43", "5"], ["South", "21", "2"], ["North", "15", "2"], ["West", "7", "1"]]),
    "groupby italian": ((13, 5), 'GROUPBY([.A2:.A6];[.C2:.C6];"MEDIA";0;0)', 3, 2,
                        [["North", "7.5"], ["South", "10.5"], ["West", "7"]]),
    "groupby documented example": ((18, 5), 'GROUPBY([.A1:.A6];[.C1:.C6];"SUM";;;-2)', 5, 2,
                                   [["Region", "Sum of Sales"], ["South", "21"], ["North", "15"], ["West", "7"],
                                    ["Total", "43"]]),
    "pivotby": ((1, 8), 'PIVOTBY([.A1:.A6];[.B1:.B6];[.C1:.C6];"SUM")', 5, 4,
                [["Region", "A", "B", "Total"], ["North", "10", "5", "15"], ["South", "1", "20", "21"],
                 ["West", "7", "", "7"], ["Total", "18", "25", "43"]]),
    "percentof": ((9, 1), "PERCENTOF([.C2:.C3];[.C2:.C6])", 1, 1, [["0.6976"]]),
    "regextest": ((10, 1), 'REGEXTEST("Riot Office";"off";1)', 1, 1, [["1"]]),
    "regextest range": ((14, 1), 'REGEXTEST([.A2:.A3];"^N")', 2, 1, [["1"], ["0"]]),
    "regexextract": ((11, 1), 'REGEXEXTRACT("tel 055 1234";"\\d{3}")', 1, 1, [["055"]]),
    "regexextract all": ((11, 2), 'REGEXEXTRACT("tel 055 1234";"\\d{3}";1)', 1, 2, [["055", "123"]]),
    "regexreplace": ((12, 1), 'REGEXREPLACE("Ada Lovelace";"(\\w+) (\\w+)";"$2, $1")', 1, 1, [["Lovelace, Ada"]]),
}


def cell(value) -> str:
    if isinstance(value, (int, float)):
        return f'<table:table-cell office:value-type="float" office:value="{value}"><text:p>{value}</text:p></table:table-cell>'
    return f'<table:table-cell office:value-type="string"><text:p>{escape(value)}</text:p></table:table-cell>'


def fods() -> str:
    grid: dict[tuple[int, int], str] = {}
    for r, row in enumerate(DATA, 1):
        for c, value in enumerate(row, 1):
            grid[(r, c)] = cell(value)
    for (r0, c0), formula, height, width, _ in CASES.values():
        spans = f' table:number-matrix-rows-spanned="{height}" table:number-matrix-columns-spanned="{width}"' \
            if height * width > 1 else ""
        grid[(r0, c0)] = f"<table:table-cell table:formula={quoteattr('of:=' + PREFIX + formula)}{spans}/>"
        for r in range(r0, r0 + height):
            for c in range(c0, c0 + width):
                if (r, c) != (r0, c0):
                    grid[(r, c)] = "<table:covered-table-cell/>"
    rows = max(r for r, _ in grid)
    cols = max(c for _, c in grid)
    body = "".join("<table:table-row>" + "".join(grid.get((r, c), "<table:table-cell/>") for c in range(1, cols + 1))
                   + "</table:table-row>" for r in range(1, rows + 1))
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<office:document xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
            'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
            'xmlns:of="urn:oasis:names:tc:opendocument:xmlns:of:1.2" office:version="1.3" '
            'office:mimetype="application/vnd.oasis.opendocument.spreadsheet"><office:body><office:spreadsheet>'
            f'<table:table table:name="Sheet1">{body}</table:table></office:spreadsheet></office:body></office:document>')


def block(grid: list[list[str]], r0: int, c0: int, height: int, width: int) -> list[list[str]]:
    return [[(grid[r - 1][c - 1] if r - 1 < len(grid) and c - 1 < len(grid[r - 1]) else "")
             for c in range(c0, c0 + width)] for r in range(r0, r0 + height)]


def same(got: list[list[str]], expected: list[list[str]]) -> bool:
    def eq(a: str, b: str) -> bool:
        try:
            return abs(float(a) - float(b)) < 1e-4
        except ValueError:
            return a == b
    return len(got) == len(expected) and all(len(g) == len(e) and all(eq(x, y) for x, y in zip(g, e))
                                             for g, e in zip(got, expected))


def main() -> int:
    soffice = Path(sys.argv[1])
    work = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(tempfile.mkdtemp(prefix="riot-xf-"))
    work.mkdir(parents=True, exist_ok=True)
    profile = (work / "profile").as_uri()
    subprocess.run([sys.executable, str(ROOT / "addins" / "calc" / "build_oxt.py"), "--out", str(work / "dist")], check=True)
    oxt = next((work / "dist").glob("*.oxt"))
    unopkg = soffice.with_name("unopkg.com" if sys.platform == "win32" and soffice.with_name("unopkg.com").exists() else "unopkg")
    # On Windows soffice.exe detaches at once; soffice.com is the console twin that waits for the conversion.
    console = soffice.with_suffix(".com") if sys.platform == "win32" and soffice.with_suffix(".com").exists() else soffice
    done = subprocess.run([str(unopkg), "add", "--suppress-license", f"-env:UserInstallation={profile}", str(oxt)],
                          capture_output=True, text=True, timeout=300)
    print(done.stdout, done.stderr)
    if done.returncode:
        return 1
    source = work / "functions.fods"
    source.write_text(fods(), encoding="utf-8")
    out = work / "out"
    conv = subprocess.run([str(console), f"-env:UserInstallation={profile}", "--headless", "--norestore", "--convert-to", "csv",
                           "--outdir", str(out), str(source)], capture_output=True, text=True, timeout=300)
    print(conv.stdout, conv.stderr)
    csv_path = out / "functions.csv"
    if not csv_path.exists():
        return 1
    grid = list(csv.reader(io.StringIO(csv_path.read_text(encoding="utf-8"))))
    print("\n".join(",".join(r) for r in grid))
    failures = 0
    for name, ((r0, c0), _, height, width, expected) in CASES.items():
        got = block(grid, r0, c0, height, width)
        ok = same(got, expected)
        failures += not ok
        print(f"[ok] {name}" if ok else f"[FAIL] {name}\n   expected {expected}\n   got      {got}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
