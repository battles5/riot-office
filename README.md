<p align="center">
  <img src="assets/banner.png" alt="RIOT OFFICE — loud colours, local files">
</p>

<h1 align="center"><img src="assets/icon.png" width="40" alt=""> RIOT OFFICE</h1>

<p align="center">
  <em>ｌｏｕｄ　ｃｏｌｏｕｒｓ，　ｌｏｃａｌ　ｆｉｌｅｓ</em> — a desktop office suite that lives on your PC, built on LibreOffice.<br>
  <a href="https://github.com/battles5/riot-office/releases/latest"><strong>Download for Windows or Ubuntu</strong></a>
  ·
  <a href="docs/Guide.html">User guide</a>
  ·
  <a href="docs/COMPATIBILITY.md">Compatibility</a>
  ·
  <a href="docs/ROADMAP.md">Roadmap</a>
  ·
  <a href="CHANGELOG.md">Changelog</a>
</p>

<p align="center">
  <img alt="License MIT-0" src="https://img.shields.io/badge/license-MIT--0-ff2975">
  <img alt="Windows 10/11" src="https://img.shields.io/badge/Windows-10%20%7C%2011-2de2e6">
  <img alt="Ubuntu 24.04+" src="https://img.shields.io/badge/Ubuntu-24.04%2B-2de2e6">
  <img alt="Build" src="https://github.com/battles5/riot-office/actions/workflows/build.yml/badge.svg">
  <img alt="LibreOffice 26.8" src="https://img.shields.io/badge/LibreOffice-26.8-ffd640">
  <img alt="English and Italian" src="https://img.shields.io/badge/languages-EN%20%7C%20IT-ffd640">
  <img alt="Offline" src="https://img.shields.io/badge/works-100%25%20offline-b026ff">
</p>

---

Riot Office is what office software used to be: you install it, it runs on your computer, your
files stay on your disk. No account, no cloud, no subscription.

Under the hood it is **LibreOffice**, unmodified, set up to feel like the Office most people know:
documents, spreadsheets and presentations are saved as `.docx`, `.xlsx` and `.pptx` by default,
with the tabbed interface, fonts that keep Calibri and Cambria documents on the same pages, and
English or Italian at the click of a menu. Around it, a synthwave launcher with PDF tools and two
helpers for anyone moving away from Microsoft Office: an **inventory** that tells you which files
will need attention, and a **fidelity check** that measures how close the result is.

| You know | In Riot Office | |
|---|---|---|
| Word | **Riot Writer** | LibreOffice Writer |
| Excel | **Riot Calc** | LibreOffice Calc |
| PowerPoint | **Riot Impress** | LibreOffice Impress |
| Acrobat | **Riot PDF** | PDF tools in the launcher today; a full editor is [on the roadmap](docs/ROADMAP.md) |

## Why "riot"?

- **A riot of colour.** Neon pink, cyan and yellow over a striped sunset: office software does not
  have to be grey.
- **A quiet riot against lock-in.** Your documents, your disk, open formats underneath. Nothing is
  uploaded, nothing expires, nothing needs a licence server.
- **Do it yourself.** Like a punk record, it is made from parts anyone can get: free software,
  assembled and tuned, not rewritten.

## Features

- **LibreOffice 26.8, tuned for Office users** (one configuration layer, the same on both systems):
  - new files saved as `.docx` / `.xlsx` / `.pptx`, with no "keep current format?" question;
  - tabbed, ribbon-like interface in Writer, Calc and Impress;
  - only trusted or signed macros run;
  - nothing leaves the PC: no update check, no crash report upload;
  - every setting can still be changed by the user.
- **English and Italian**: launcher, setup wizard, menu entries, LibreOffice's interface and help.
  The *Language* menu switches the launcher and LibreOffice together.
- **Fonts**: Carlito and Caladea, metric-compatible with Calibri and Cambria, so pages break where
  they did in Word. Aptos (Office's newer default, no free clone yet) falls back to Carlito.
- **Launcher**: Writer, Calc, Impress, open any file, and PDF tools — merge, split, rotate,
  convert to PDF or **PDF/A-2b** for archiving, **OCR** to make scans searchable (with
  OCRmyPDF and Tesseract installed).
- **Compatibility inventory**: point it at a folder or a whole share. It finds VBA macros,
  Power Query, Power Pivot data models, slicers, pivot tables, Excel functions Calc does not have
  yet, Aptos fonts, SmartArt and encrypted files, without opening or running anything.
- **Fidelity check**: export a set of documents to PDF from Microsoft Office once; Riot Office
  converts the same documents and reports page counts and text similarity, file by file.
- **Installers for Windows and Ubuntu**, built and tested on clean machines by GitHub Actions for
  every change.

## Excel users, read this first

Calc covers pivot tables, filters, conditional formatting and the modern dynamic-array functions
(XLOOKUP, FILTER, SORT, UNIQUE, LET, VSTACK, TEXTSPLIT, ...). LAMBDA and its friends arrive with
LibreOffice 27.2 (February 2027). **Power Query, Power Pivot / Data Model, GROUPBY / PIVOTBY and
slicers are not available**, and VBA macros run only in part. Run the inventory on your files
before switching: see [docs/COMPATIBILITY.md](docs/COMPATIBILITY.md).

## Requirements

|  | Windows | Ubuntu |
|---|---|---|
| System | Windows 10/11 64-bit (x64) | Ubuntu 24.04 or 26.04 (Debian 12+ works too) |
| Rights | administrator (LibreOffice installs per machine) | `sudo` |
| Disk | about 1.2 GB | about 600 MB with dependencies |
| Internet | not needed: the setup contains everything | only to download packages from the Ubuntu archive |

## Installation

### Windows

1. Download `RiotOffice-Setup-<version>.exe` from the
   [Releases](https://github.com/battles5/riot-office/releases/latest).
2. Run it. The setup is not digitally signed yet: if Windows shows "Windows protected your PC",
   choose *More info* → *Run anyway*.
3. Pick English or Italian and follow the wizard. It installs LibreOffice (skipped when the same
   version is already there), the fonts, the Riot configuration and the launcher.

The Start menu gets *Riot Office*, *Riot Writer*, *Riot Calc*, *Riot Impress* and the guide.
`.docx`, `.xlsx`, `.pptx` and the older Office formats open with LibreOffice.

Silent install for IT departments:

```
RiotOffice-Setup-0.1.0.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /LANG=it
```

### Ubuntu

```bash
sudo apt install ./riot-office_0.1.0_all.deb
```

`apt` pulls LibreOffice, the Italian language pack, the fonts and the dictionaries from Ubuntu's
archive, so they keep getting Ubuntu's security updates. Ubuntu 24.04 ships an older LibreOffice
(24.2); for 26.8 add the LibreOffice PPA first:

```bash
sudo add-apt-repository ppa:libreoffice/ppa
```

## Usage

Open **Riot Office** from the menu: pick Writer, Calc or Impress, or a PDF tool. The *Language*
menu switches between English and Italian (LibreOffice follows at its next start).

The same tools on the command line:

```bash
riot-office doctor                                   # is everything in place?
riot-office open calc budget.xlsx                    # open a file
riot-office convert *.docx --to pdf --pdfa           # PDF/A-2b for archiving
riot-office pdf merge all.pdf a.pdf b.pdf            # merge, split, rotate, ocr
riot-office inventory //server/share --out inventory.md --csv inventory.csv
riot-office fidelity corpus/ office-pdfs/ --out fidelity.md
riot-office language it                              # Italian everywhere
```

On Windows the command is `"C:\Program Files\Riot Office\runtime\python.exe" -m riot_office`.

## How it is built

```
riot_office/       launcher (Tk), command line, LibreOffice helpers, PDF tools, inventory, fidelity
config/            riot-office*.xcd: the LibreOffice configuration layers (common + one per module)
installer/         Windows setup (Inno Setup + PowerShell) and Ubuntu .deb, pinned downloads
assets/            artwork and the script that draws it
docs/              guide, compatibility matrix, roadmap, strategy
ci/                checks run by GitHub Actions on real installs
```

Run from source (Python 3.10+, LibreOffice installed):

```bash
python -m pip install -e .[dev]
python -m pytest
python -m riot_office
```

Build the installers: `bash installer/linux/build_deb.sh` on Linux,
`installer\windows\build_installer.ps1` on Windows (needs Inno Setup 6). Redraw the artwork with
`python assets/make_art.py`.

The [strategy](docs/STRATEGY.md) explains the choices: why LibreOffice is distributed and
configured rather than forked, and why the PDF editor will be built on PDF4QT.

## Licence

Riot Office's own files are under **MIT No Attribution** ([LICENSE.txt](LICENSE.txt)).
LibreOffice (MPL-2.0), the fonts (SIL OFL 1.1), Python and pypdf keep their own licences: see
[THIRD-PARTY-NOTICES](installer/THIRD-PARTY-NOTICES.txt).

Riot Office is an independent distribution *based on LibreOffice*. It is not affiliated with or
endorsed by The Document Foundation, Microsoft or Adobe; their product names are used only to
describe file compatibility.
