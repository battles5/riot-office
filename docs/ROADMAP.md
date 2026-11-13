# Roadmap

## 0.1 — the suite (this release)

- LibreOffice 26.8.3 distributed and configured for Office users, English and Italian.
- Synthwave launcher, PDF tools (merge, split, rotate, convert, PDF/A, OCR).
- Compatibility inventory and fidelity check.
- Windows setup and Ubuntu package, tested on clean machines by CI.

## 0.2 — trial and polish

- Fidelity check with pixel comparison (SSIM per page) next to text and page count.
- Inventory: Office add-ins and external links; HTML report.
- Launcher: recent files, drag and drop onto the window.
- Riot templates (letter, report, budget, slide deck) in English and Italian.
- Code signing for the Windows setup.

## 0.3 — LibreOffice 27.2

- Move to LibreOffice 27.2 (LAMBDA, MAP, REDUCE, SCAN, BYROW, BYCOL in Calc).
- Offline update channel: an internal folder or APT repository the launcher checks.

## Riot PDF — a desktop PDF editor

The Acrobat-like application, built as a fork of **[PDF4QT](https://github.com/JakubMelka/PDF4QT)**
(MIT, C++/Qt 6): the most complete open-source desktop PDF suite, with viewer, annotations, text
editing, page organiser, compare, redaction, OCR, forms and encryption already in place.

Work planned on top of it, as plugins rather than core patches so upstream updates stay easy:

1. **Italian translation** of the interface (it has none today) and a Riot theme.
2. **Riot Firma** — Italian digital signatures:
   - smart cards and tokens (CNS and the main qualified providers) through PKCS#11
     (OpenSC plus the vendor's middleware) on Windows and Ubuntu, and the Windows certificate store;
   - **PAdES** signatures (B-B, B-T with a time-stamping service, B-LT) and **CAdES `.p7m`** envelopes;
   - verification with the **EU DSS** library against the EU and Italian trusted lists, with a
     report in English and Italian.
3. Batch OCR and PDF/A with OCRmyPDF; PDF/A validation with veraPDF.
4. Windows MSI and Ubuntu package, launched from the Riot Office launcher and set as the default
   PDF application.

Known limits, also in the plan: editing existing text with paragraph reflow, PDF → Word
conversion and dynamic XFA forms will stay behind Acrobat for a long time.

Signatures need the network for three things only — time stamps, revocation checks and trusted
list updates. Everything else works offline.
