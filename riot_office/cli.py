"""Command line of Riot Office. Without arguments it opens the launcher window.

    riot-office                         the launcher window
    riot-office open calc [FILES]       open a LibreOffice module or files
    riot-office doctor                  check LibreOffice, configuration, fonts, OCR
    riot-office config install          install the Riot configuration (administrator/root)
    riot-office language it             interface language of Riot Office and LibreOffice
    riot-office convert FILES --to pdf  convert with LibreOffice headless (--pdfa for PDF/A-2b)
    riot-office pdf merge OUT IN...     merge, split, rotate, ocr
    riot-office inventory FOLDER        what in a folder of Office files needs attention
    riot-office fidelity CORPUS REFS    compare LibreOffice's PDFs with Microsoft Office's
"""

import argparse
import shutil
import sys
from pathlib import Path

from . import APP_NAME, __version__, config, i18n, libreoffice, pdftools


def _need_libreoffice() -> libreoffice.Installation:
    inst = libreoffice.find()
    if inst is None:
        raise SystemExit("LibreOffice not found. Install it, or set RIOT_SOFFICE to the soffice executable.")
    return inst


def _font_installed(family: str) -> bool:
    """True when a font family is installed (fc-list on Linux, the Fonts folders on Windows)."""
    if sys.platform == "win32":
        import os

        folders = [Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts",
                   Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Windows" / "Fonts"]
        return any(folder.glob(f"{family}*.ttf") for folder in folders if folder.is_dir())
    if shutil.which("fc-list"):
        import subprocess

        out = subprocess.run(["fc-list", ":", "family"], capture_output=True, text=True).stdout
        return any(family.lower() in line.lower() for line in out.splitlines())
    return False


def cmd_doctor(args) -> int:
    print(f"{APP_NAME} {__version__}")
    problems = 0
    inst = libreoffice.find()
    if inst is None:
        print("  [!!] LibreOffice: not found")
        return 1
    print(f"  [ok] LibreOffice {inst.version() or '(version unknown)'}: {inst.soffice}")
    if config.is_installed(inst):
        print(f"  [ok] Riot configuration: {config.installed_path(inst)}")
    else:
        problems += 1
        print(f"  [!!] Riot configuration missing or outdated: run 'riot-office config install' as administrator")
    for family in ("Carlito", "Caladea"):
        if _font_installed(family):
            print(f"  [ok] font {family}")
        else:
            problems += 1
            print(f"  [!!] font {family} missing (metric-compatible with "
                  f"{'Calibri' if family == 'Carlito' else 'Cambria'})")
    print(f"  [{'ok' if pdftools.ocr_available() else '--'}] OCR (OCRmyPDF + Tesseract)"
          f"{'' if pdftools.ocr_available() else ': optional, not installed'}")
    locale = config.get_ui_locale()
    print(f"  [ok] interface language: Riot Office {i18n.get_language()}, LibreOffice {locale or 'system default'}")
    return 1 if problems else 0


def cmd_open(args) -> int:
    inst = _need_libreoffice()
    module = args.module if args.module in libreoffice.MODULES else None
    files = [Path(f) for f in args.files]
    if args.module and module is None:
        files.insert(0, Path(args.module))
    libreoffice.launch(inst, module, files)
    return 0


def cmd_config(args) -> int:
    inst = _need_libreoffice()
    if args.action == "install":
        try:
            print(f"installed {config.install(inst, Path(args.source) if args.source else config.CONFIG_XCD)}")
        except PermissionError:
            raise SystemExit("permission denied: run as administrator (Windows) or with sudo (Linux)")
    elif args.action == "uninstall":
        print("removed" if config.uninstall(inst) else "nothing to remove")
    else:
        print("installed" if config.is_installed(inst) else "not installed")
        return 0 if config.is_installed(inst) else 1
    return 0


def cmd_language(args) -> int:
    if not args.code:
        print(f"Riot Office: {i18n.get_language()}  LibreOffice: {config.get_ui_locale() or 'system default'}")
        return 0
    i18n.set_language(args.code)
    path = config.set_ui_locale(i18n.LIBREOFFICE_LOCALES[args.code])
    print(f"language set to {i18n.LANGUAGES[args.code]} (LibreOffice profile: {path})")
    return 0


def cmd_convert(args) -> int:
    inst = _need_libreoffice()
    files = [Path(f) for f in args.files]
    out_dir = Path(args.out) if args.out else files[0].parent
    for dest in libreoffice.convert(inst, files, out_dir, args.to, pdfa=args.pdfa):
        print(dest)
    return 0


def cmd_pdf(args) -> int:
    if args.action == "merge":
        print(pdftools.merge([Path(f) for f in args.inputs], Path(args.output)))
    elif args.action == "split":
        src = Path(args.input)
        for dest in pdftools.split(src, Path(args.out) if args.out else src.parent, args.ranges):
            print(dest)
    elif args.action == "rotate":
        print(pdftools.rotate(Path(args.input), Path(args.output), args.degrees, args.pages))
    elif args.action == "ocr":
        print(pdftools.ocr(Path(args.input), Path(args.output), args.lang, pdfa=not args.no_pdfa))
    return 0


def cmd_inventory(args) -> int:
    from . import inventory

    root = Path(args.folder)
    reports = inventory.scan(root)
    report = inventory.markdown(reports, root)
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"report: {args.out}")
    else:
        print(report)
    if args.csv:
        inventory.write_csv(reports, Path(args.csv), root)
        print(f"csv: {args.csv}")
    return 0


def cmd_fidelity(args) -> int:
    from . import fidelity

    inst = _need_libreoffice()
    corpus = Path(args.corpus)
    results = fidelity.compare(inst, corpus, Path(args.references), Path(args.keep) if args.keep else None)
    report = fidelity.markdown(results, corpus)
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"report: {args.out}")
    else:
        print(report)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="riot-office", description=f"{APP_NAME}: a local office suite on LibreOffice.")
    parser.add_argument("--version", action="version", version=f"{APP_NAME} {__version__}")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("gui", help="open the launcher window (the default)")
    p = sub.add_parser("open", help="open a LibreOffice module (writer, calc, impress, draw) or files")
    p.add_argument("module", nargs="?")
    p.add_argument("files", nargs="*")
    p.set_defaults(func=cmd_open)

    sub.add_parser("doctor", help="check the installation").set_defaults(func=cmd_doctor)

    p = sub.add_parser("config", help="install, remove or check the Riot configuration of LibreOffice")
    p.add_argument("action", choices=("install", "uninstall", "status"))
    p.add_argument("--source", help="a different .xcd file to install")
    p.set_defaults(func=cmd_config)

    p = sub.add_parser("language", help="show or set the interface language (Riot Office and LibreOffice)")
    p.add_argument("code", nargs="?", choices=tuple(i18n.LANGUAGES))
    p.set_defaults(func=cmd_language)

    p = sub.add_parser("convert", help="convert documents with LibreOffice headless")
    p.add_argument("files", nargs="+")
    p.add_argument("--to", default="pdf", help="target extension: pdf, docx, xlsx, pptx, odt, ... (default pdf)")
    p.add_argument("--pdfa", action="store_true", help="PDF/A-2b, for archiving")
    p.add_argument("--out", help="output folder (default: next to the first file)")
    p.set_defaults(func=cmd_convert)

    p = sub.add_parser("pdf", help="PDF tools")
    pdf = p.add_subparsers(dest="action", required=True)
    m = pdf.add_parser("merge", help="merge PDFs in order")
    m.add_argument("output")
    m.add_argument("inputs", nargs="+")
    s = pdf.add_parser("split", help="split a PDF by page ranges (default: one file per page)")
    s.add_argument("input")
    s.add_argument("--ranges", default="", help='for example "1-3,4-10"')
    s.add_argument("--out", help="output folder")
    r = pdf.add_parser("rotate", help="rotate pages clockwise")
    r.add_argument("input")
    r.add_argument("output")
    r.add_argument("--degrees", type=int, default=90, choices=(90, 180, 270))
    r.add_argument("--pages", default="", help='for example "1,3-5" (default: all)')
    o = pdf.add_parser("ocr", help="add a searchable text layer (needs OCRmyPDF and Tesseract)")
    o.add_argument("input")
    o.add_argument("output")
    o.add_argument("--lang", default="ita+eng", help="Tesseract languages (default ita+eng)")
    o.add_argument("--no-pdfa", action="store_true", help="plain PDF instead of PDF/A")
    p.set_defaults(func=cmd_pdf)

    p = sub.add_parser("inventory", help="scan Office files for macros, Power Query, missing functions, fonts")
    p.add_argument("folder")
    p.add_argument("--out", help="Markdown report file (default: print it)")
    p.add_argument("--csv", help="also write one CSV row per file")
    p.set_defaults(func=cmd_inventory)

    p = sub.add_parser("fidelity", help="compare LibreOffice's rendering with reference PDFs from Microsoft Office")
    p.add_argument("corpus", help="folder of documents")
    p.add_argument("references", help="folder of PDFs exported from Microsoft Office, same names and subfolders")
    p.add_argument("--out", help="Markdown report file (default: print it)")
    p.add_argument("--keep", help="keep LibreOffice's PDFs in this folder")
    p.set_defaults(func=cmd_fidelity)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command in (None, "gui"):
        from .gui import run

        return run()
    try:
        return args.func(args)
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
