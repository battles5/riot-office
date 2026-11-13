# Strategy

Why Riot Office is built the way it is. Written in November 2026.

## The goal

Equivalents of Word, Excel (including its data features), PowerPoint and Acrobat that are
**installed on Windows and Ubuntu PCs and run locally**, like office software used to: no cloud,
no server, no subscription. English and Italian from the first release.

## The decision: distribute, don't rewrite

Office and Acrobat are worth what they are because of decades of file-format edge cases — page
layout, formula semantics, PDF rendering, signatures — not because of their buttons. Re-creating
that is out of reach for a small team, and unnecessary: LibreOffice already does it, with a large
community and two releases a year.

So Riot Office **does not fork LibreOffice**. It ships the official, unmodified LibreOffice and
changes only what LibreOffice lets anyone change:

- a configuration layer (`config/riot-office.xcd`) for Office-like defaults;
- fonts, language packs and dictionaries;
- a launcher, PDF tools and migration helpers around it;
- the installers.

A fork of LibreOffice's core (about 10 million lines of C++) would need a permanent team just to
merge upstream releases and security fixes every few weeks. Bugs Riot Office runs into are
reported, and where it matters fixed, **upstream**, so everyone benefits and nothing has to be
maintained twice.

### What this means for the name

The suite is "Riot Office — based on LibreOffice". The Riot brand lives on the launcher, icons,
installer and (later) the PDF editor; LibreOffice's own windows keep its name, as its trademark
policy requires for unmodified builds. Rebuilding LibreOffice with Riot branding inside is
possible later (configure `--with-branding`), but it means owning a Windows and Linux build
pipeline for every release; it is not worth it before the suite has proven itself.

## Components

| Need | Component | Why |
|---|---|---|
| Word / Excel / PowerPoint | LibreOffice 26.8 Writer, Calc, Impress | Best free OOXML support; same engine on Windows and Ubuntu |
| Office look and defaults | `riot-office.xcd` | One file, same on both systems, defaults not locks |
| Fonts | Carlito, Caladea (+ Liberation on Ubuntu) | Metric-compatible with Calibri, Cambria, Arial, Times |
| PDF basics | pypdf, LibreOffice export, OCRmyPDF + Tesseract | Permissive licences, already proven |
| Full PDF editor | PDF4QT fork + Riot Firma (see [ROADMAP](ROADMAP.md)) | MIT-licensed, most complete open-source desktop PDF suite |
| Windows setup | Inno Setup bundling the LibreOffice MSI | Offline, silent install for IT, English and Italian wizard |
| Ubuntu package | `.deb` depending on the distribution's LibreOffice | Security updates keep flowing from Ubuntu; no snap (smart cards need native packages) |

## Known gaps, stated up front

- **Excel**: Power Query, Power Pivot / Data Model, GROUPBY / PIVOTBY and slicers are missing;
  LAMBDA arrives with LibreOffice 27.2; VBA runs only in part. Measure with the inventory; keep a
  few Excel licences where they are really needed.
- **Fonts**: Aptos has no free metric clone yet.
- **PDF**: paragraph-level text editing, PDF → Word and dynamic XFA forms will stay behind Acrobat.
- **Signatures** need a network connection for time stamps and revocation checks.

## How to adopt it

1. **Try** (4–6 weeks): install on 10–20 PCs, run `riot-office inventory` on the shared folders
   and `riot-office fidelity` on a few hundred real documents with PDFs exported from Office.
   Decide how many Office and Acrobat licences to keep.
2. **Roll out** (3–4 months): signed setup, internal update folder or APT repository, the Riot
   configuration pushed by policy if needed (LibreOffice reads Windows Group Policy under
   `HKLM\Software\Policies\LibreOffice`). Office stays installed in parallel for a while.
3. **Riot PDF with signatures** (6–9 months, in parallel): the PDF4QT-based editor and the
   Italian signature module, tested with real smart cards from several providers.

Steady state: about two to three people for monthly updates, security fixes and support.
LibreOffice point releases arrive every few weeks and fix bugs triggered by malicious
documents — apply them promptly, after a short pilot.

## Rules

- No reverse engineering or decompilation of Microsoft or Adobe software. Compatibility comes from
  the published specifications (ECMA-376 / ISO 29500, Microsoft's Open Specifications, ISO 32000
  for PDF) and from LibreOffice's existing filters.
- Original names and artwork: nothing that imitates Word, Excel, PowerPoint or Acrobat.
- No Microsoft fonts in the installers.
- Permissive or weak-copyleft components inside Riot's own programs; GPL/AGPL tools only as
  separate, unmodified programs.
- Distributing Riot Office to third parties brings obligations (licence notices, the EU Cyber
  Resilience Act from 2027): check them before doing so.
