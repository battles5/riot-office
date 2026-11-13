# Changelog

## 0.1.0 — 2026-11-13

First release.

- **Riot Office = LibreOffice 26.8.3, set up like a classic local Office.** Writer, Calc and
  Impress save as `.docx` / `.xlsx` / `.pptx` by default, never ask "keep current format?",
  use the tabbed (ribbon-like) interface, run only trusted macros, and never phone home
  (no update check, no crash report upload). One configuration layer, `config/riot-office.xcd`,
  identical on Windows and Ubuntu; users can still change every setting.
- **English and Italian** from day one: the launcher, the Windows setup wizard, the Linux menu
  entries and LibreOffice itself (interface and help). The Language menu switches the launcher
  and LibreOffice together.
- **Fonts**: Carlito and Caladea (metric-compatible with Calibri and Cambria) installed on both
  systems; Aptos, which has no free clone yet, is drawn with Carlito when missing.
- **Synthwave launcher**: Writer, Calc, Impress, "open a file" and the first PDF tools —
  merge, split, rotate, convert to PDF or PDF/A-2b, OCR (with OCRmyPDF and Tesseract when
  installed).
- **Command line** `riot-office`: `open`, `doctor`, `config`, `language`, `convert`, `pdf`,
  `inventory`, `fidelity`.
- **Compatibility inventory**: scans a folder of Office files for VBA macros, Power Query,
  Power Pivot data models, slicers, pivot tables, Excel functions Calc lacks (or gets in 27.2),
  Aptos fonts, SmartArt and encrypted files. Markdown and CSV reports.
- **Fidelity check**: converts a corpus with LibreOffice and compares it with PDFs exported from
  Microsoft Office (page count and text similarity).
- **Installers**: `RiotOffice-Setup-0.1.0.exe` for Windows 10/11 (bundles LibreOffice, help in
  both languages, fonts, a private Python) and `riot-office_0.1.0_all.deb` for Ubuntu 24.04+
  (LibreOffice, fonts and dictionaries from the distribution).
- **CI**: both installers are built, installed and tested on clean machines for every push;
  LibreOffice is queried over UNO to prove it sees the configuration.
