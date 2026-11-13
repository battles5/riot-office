"""Compatibility inventory: scan a folder of Office files for what LibreOffice handles only partly.

Nothing is executed or converted: the files are opened as ZIP (OOXML) or scanned as bytes
(legacy binary formats), so the scan is fast and safe on large shares. Findings:

- macros (VBA projects in docm/xlsm/pptm or in legacy doc/xls/ppt);
- Power Query queries and the Power Pivot data model (no equivalent in Calc);
- slicers and timelines, pivot tables, external data connections;
- Excel functions that Calc does not have yet, or only from a later version;
- references to Microsoft fonts without a free metric clone (Aptos);
- SmartArt diagrams;
- encrypted files (which cannot be scanned).
"""

import csv
import re
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

OOXML = {".docx", ".docm", ".dotx", ".dotm", ".xlsx", ".xlsm", ".xltx", ".xltm", ".pptx", ".pptm", ".potx", ".potm"}
LEGACY = {".doc", ".dot", ".xls", ".xlt", ".ppt", ".pot"}
OTHER = {".xlsb", ".vsd", ".vsdx", ".pub", ".mpp", ".one", ".accdb", ".mdb"}
OLE_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"

# Excel functions by Calc support. Names appear in OOXML formulas as _xlfn.NAME (or _xlfn._xlws.NAME).
LATER_FUNCTIONS = {  # merged in LibreOffice master in 2026, expected in 27.2 (February 2027)
    "LAMBDA", "MAP", "REDUCE", "SCAN", "BYROW", "BYCOL", "MAKEARRAY", "ISOMITTED",
}
MISSING_FUNCTIONS = {  # no implementation in Calc as of 26.8
    "GROUPBY", "PIVOTBY", "PERCENTOF", "TRIMRANGE", "REGEXTEST", "REGEXREPLACE", "REGEXEXTRACT",
    "IMAGE", "STOCKHISTORY", "TRANSLATE", "DETECTLANGUAGE", "COPILOT", "PY",
}
FUNCTION_RE = re.compile(rb"_xlfn\.(?:_xlws\.)?([A-Z][A-Z0-9.]*)\(")

FINDINGS = {
    "macros": "VBA macros (partly supported; plan a rewrite in Basic or Python)",
    "power_query": "Power Query queries (not refreshable in Calc)",
    "data_model": "Power Pivot data model (not supported in Calc)",
    "slicers": "Slicers or timelines (not supported in Calc)",
    "pivot_tables": "Pivot tables (supported; check layout and calculated fields)",
    "external_connections": "External data connections (check them by hand)",
    "functions_later": "Excel functions expected in LibreOffice 27.2",
    "functions_missing": "Excel functions not available in Calc",
    "aptos_font": "Aptos font (no free metric clone; layout may change)",
    "smartart": "SmartArt diagrams (shown as a picture fallback, not editable)",
    "encrypted": "Encrypted or password-protected (could not be scanned)",
    "unreadable": "Damaged or unreadable file",
    "not_supported_format": "Format with read-only or no support in LibreOffice",
}


@dataclass
class FileReport:
    """What was found in one file."""

    path: Path
    findings: set[str] = field(default_factory=set)
    functions: set[str] = field(default_factory=set)

    @property
    def ok(self) -> bool:
        return not (self.findings - {"pivot_tables"})


def _scan_ooxml(path: Path, report: FileReport) -> None:
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        with open(path, "rb") as f:
            head = f.read(8)
        report.findings.add("encrypted" if head == OLE_MAGIC else "unreadable")
        return
    with archive:
        names = archive.namelist()
        lower = [n.lower() for n in names]
        if any(n.endswith("vbaproject.bin") for n in lower):
            report.findings.add("macros")
        if any(n.startswith("xl/model/") for n in lower):
            report.findings.add("data_model")
        if any(n.startswith(("xl/slicers/", "xl/slicercaches/", "xl/timelines/", "xl/timelinecaches/")) for n in lower):
            report.findings.add("slicers")
        if any(n.startswith("xl/pivottables/") for n in lower):
            report.findings.add("pivot_tables")
        if any("/diagrams/" in n for n in lower):
            report.findings.add("smartart")
        for name in names:
            low = name.lower()
            if not low.endswith((".xml", ".rels")):
                continue
            data = archive.read(name)
            if low == "xl/connections.xml":
                report.findings.add("power_query" if b"Microsoft.Mashup" in data else "external_connections")
            if low.startswith("customxml/") and b"DataMashup" in data:
                report.findings.add("power_query")
            if low.startswith("xl/worksheets/") or low.startswith("xl/definednames") or low == "xl/workbook.xml":
                for match in FUNCTION_RE.finditer(data):
                    fn = match.group(1).decode("ascii")
                    if fn in LATER_FUNCTIONS:
                        report.findings.add("functions_later")
                        report.functions.add(fn)
                    elif fn in MISSING_FUNCTIONS:
                        report.findings.add("functions_missing")
                        report.functions.add(fn)
            if b"Aptos" in data and ("theme" in low or "styles" in low or "fonttable" in low or "document.xml" in low):
                report.findings.add("aptos_font")


def _scan_legacy(path: Path, report: FileReport) -> None:
    data = path.read_bytes()
    if not data.startswith(OLE_MAGIC):
        report.findings.add("unreadable")
        return
    # Stream names in the compound file directory are UTF-16LE.
    if "_VBA_PROJECT".encode("utf-16-le") in data or "Macros".encode("utf-16-le") in data:
        report.findings.add("macros")
    if "EncryptionInfo".encode("utf-16-le") in data:
        report.findings.add("encrypted")


def scan_file(path: Path) -> FileReport:
    """Inspect one file; unknown extensions come back with no findings."""
    report = FileReport(path)
    suffix = path.suffix.lower()
    try:
        if suffix in OOXML:
            _scan_ooxml(path, report)
        elif suffix in LEGACY:
            _scan_legacy(path, report)
        elif suffix in OTHER:
            report.findings.add("not_supported_format")
    except OSError:
        report.findings.add("unreadable")
    return report


def scan(folder: Path) -> list[FileReport]:
    """Scan every Office file under ``folder`` (Office lock files "~$..." are skipped)."""
    reports = []
    for path in sorted(folder.rglob("*")):
        if path.is_file() and not path.name.startswith("~$") and path.suffix.lower() in OOXML | LEGACY | OTHER:
            reports.append(scan_file(path))
    return reports


def write_csv(reports: list[FileReport], dest: Path, root: Path) -> None:
    with open(dest, "w", newline="", encoding="utf-8") as f:
        out = csv.writer(f)
        out.writerow(["file", "type", *FINDINGS, "functions"])
        for r in reports:
            out.writerow([r.path.relative_to(root).as_posix(), r.path.suffix.lower().lstrip("."),
                          *("yes" if key in r.findings else "" for key in FINDINGS), " ".join(sorted(r.functions))])


def markdown(reports: list[FileReport], root: Path) -> str:
    """A readable summary: totals by type and by finding, then the files that need attention."""
    by_type = Counter(r.path.suffix.lower().lstrip(".") for r in reports)
    by_finding = Counter(key for r in reports for key in r.findings)
    functions = Counter(fn for r in reports for fn in r.functions)
    lines = [f"# Compatibility inventory of `{root}`", "",
             f"**{len(reports)} files scanned**, {sum(r.ok for r in reports)} with nothing to report.", "",
             "## Files by type", "", "| Type | Files |", "|---|---:|"]
    lines += [f"| {ext} | {n} |" for ext, n in by_type.most_common()]
    lines += ["", "## Findings", "", "| Finding | Files |", "|---|---:|"]
    lines += [f"| {FINDINGS[key]} | {by_finding[key]} |" for key in FINDINGS if by_finding[key]]
    if functions:
        lines += ["", "## Excel functions to watch", "", "| Function | Files | Status |", "|---|---:|---|"]
        lines += [f"| {fn} | {n} | {'LibreOffice 27.2' if fn in LATER_FUNCTIONS else 'missing'} |"
                  for fn, n in functions.most_common()]
    attention = [r for r in reports if not r.ok]
    if attention:
        lines += ["", "## Files that need attention", ""]
        for r in attention:
            notes = ", ".join(sorted(r.findings - {"pivot_tables"}))
            extra = f" ({', '.join(sorted(r.functions))})" if r.functions else ""
            lines.append(f"- `{r.path.relative_to(root).as_posix()}`: {notes}{extra}")
    return "\n".join(lines) + "\n"
