# Compatibility

What to expect when Microsoft Office files are opened in Riot Office 0.1 (LibreOffice 26.8).
"Compatible with every file" is not a promise anyone can keep; this page says where the edges
are, and `riot-office inventory` tells you which of *your* files sit on them.

## File formats

| Level | Formats | What it means |
|---|---|---|
| **Native** | odt, ods, odp, odg, csv, tsv, txt, html, md | Open and save with no loss |
| **Good** | docx, dotx, docm, xlsx, xltx, xlsm, pptx, potx, pptm, doc, xls, ppt, rtf | Open and save; everyday documents look the same, complex ones may differ (see below) |
| **PDF export** | PDF 1.4–2.0, PDF/A-1b/2b/3b/4, PDF/UA | From any document, with `riot-office convert --pdfa` or *File → Export as PDF* |
| **Open only** | xlsb, vsd, vsdx, pub, Keynote, Pages, Numbers | Opened and converted; saved back in another format |
| **Not supported** | mpp (Project), one (OneNote), accdb/mdb (Access), msg/pst (Outlook), xps | Use other tools |

## Word → Writer

- Text, styles, headers/footers, tables, images, tracked changes, comments, fields, footnotes,
  tables of contents: good.
- Layout: most documents keep the same pages **when the fonts match**. Install Carlito and
  Caladea (done by the installers) for Calibri and Cambria. **Aptos**, Office's default since
  2024, has no free metric clone: Riot Office draws it with Carlito, so lines can wrap
  differently.
- SmartArt is shown through its picture fallback and cannot be edited.
- Word VBA macros do not run.

## Excel → Calc

| Feature | Status in Calc 26.8 |
|---|---|
| Formulas, named ranges, conditional formatting, data validation, charts, filters, subtotals | ✅ |
| Pivot tables | ✅ (check calculated fields and layout) |
| XLOOKUP, XMATCH, FILTER, SORT, SORTBY, UNIQUE, SEQUENCE, RANDARRAY, LET | ✅ |
| VSTACK, HSTACK, TAKE, DROP, TEXTSPLIT, TEXTBEFORE, TEXTAFTER, dynamic arrays (spill), `#SPILL!` | ✅ |
| LAMBDA, MAP, REDUCE, SCAN, BYROW, BYCOL, MAKEARRAY, the `#` spill reference | ⏳ LibreOffice 27.2 (February 2027) |
| GROUPBY, PIVOTBY, PERCENTOF, REGEXTEST, REGEXEXTRACT, REGEXREPLACE | ✅ **Riot add-in**: typed in Calc and saved in `.ods`; in `.xlsx` they come back as `#NAME?` ([details](EXCEL-FUNCTIONS.md)) |
| IMAGE, STOCKHISTORY, TRANSLATE, COPILOT, PY | ❌ |
| Slicers and timelines | ❌ |
| **Power Query** (Get & Transform) | ❌ the data is shown, the queries cannot be refreshed |
| **Power Pivot / Data Model / DAX** | ❌ |
| VBA macros | ⚠️ partly: simple Excel macros can run with `Option VBASupport 1`; UserForms and ActiveX are limited |
| Sheet size | 1,048,576 rows × 16,384 columns, like Excel |

**Rule of thumb:** run the inventory. Files that call `GROUPBY`, `PIVOTBY` or `REGEX*` are listed too: their
formulas have to be re-entered in Calc, which provides them through the Riot add-in. If only a few workbooks use Power Query, Power Pivot or
complex VBA, rewrite them (Calc formulas, LibreOffice Basic or Python scripts). If many do, keep a
few Excel licences for the people who maintain them: it costs far less than chasing parity.

## PowerPoint → Impress

- Slides, layouts, masters, text, images, tables, charts, notes: good.
- Most animations and transitions: good; some advanced ones are simplified.
- SmartArt: picture fallback.
- PowerPoint VBA does not run.

## PDF (Riot PDF)

| Task | Riot Office 0.1 |
|---|---|
| Merge, split, rotate pages | ✅ launcher and `riot-office pdf` |
| Office document → PDF, PDF/A-2b | ✅ |
| OCR (searchable scans) | ✅ with OCRmyPDF + Tesseract installed |
| View and annotate | LibreOffice Draw or your system viewer for now |
| Edit text, forms, redaction, compare, digital signatures (PAdES, CAdES `.p7m`) | Planned: [Riot PDF on PDF4QT](ROADMAP.md) |

## Measuring it on your own files

```bash
riot-office inventory D:\Shared --out inventory.md --csv inventory.csv
```

Then pick 200–500 representative documents, export each one to PDF from Microsoft Office into a
mirror folder, and run:

```bash
riot-office fidelity corpus/ office-pdfs/ --out fidelity.md
```

A document passes when it has the same page count and at least 95% text similarity. Re-run it at
every LibreOffice upgrade.
