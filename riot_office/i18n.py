"""Texts of the window in English and Italian, and the saved interface language.

On Linux the system Tk may draw with X core fonts, which only cover Latin-1: every text must stay
within Latin-1 there (Italian accents are fine; no "…", "—" or curly quotes).
"""

import json
import locale
import os
import sys

from .paths import DATA_DIR

SETTINGS = DATA_DIR / "settings.json"
DOTS = "…" if sys.platform == "win32" else "..."

# Interface languages, in the menu's order, with their own names.
LANGUAGES = {"en": "English", "it": "Italiano"}
# The matching LibreOffice UI locale for each interface language.
LIBREOFFICE_LOCALES = {"en": "en-US", "it": "it"}

T = {
    # --- window ---
    "tagline": {"en": "loud colours, local files", "it": "colori forti, file in locale"},
    "writer": {"en": "Writer", "it": "Writer"},
    "writer_hint": {"en": "documents  .docx  .odt", "it": "documenti  .docx  .odt"},
    "calc": {"en": "Calc", "it": "Calc"},
    "calc_hint": {"en": "spreadsheets  .xlsx  .ods", "it": "fogli di calcolo  .xlsx  .ods"},
    "impress": {"en": "Impress", "it": "Impress"},
    "impress_hint": {"en": "presentations  .pptx  .odp", "it": "presentazioni  .pptx  .odp"},
    "open_file": {"en": "Open a file{dots}", "it": "Apri un file{dots}"},
    "pdf_tools": {"en": "PDF tools", "it": "Strumenti PDF"},
    "pdf_merge": {"en": "Merge PDFs{dots}", "it": "Unisci PDF{dots}"},
    "pdf_split": {"en": "Split a PDF{dots}", "it": "Dividi un PDF{dots}"},
    "pdf_rotate": {"en": "Rotate pages{dots}", "it": "Ruota le pagine{dots}"},
    "pdf_convert": {"en": "Convert to PDF{dots}", "it": "Converti in PDF{dots}"},
    "pdf_ocr": {"en": "Make searchable (OCR){dots}", "it": "Rendi ricercabile (OCR){dots}"},
    "menu_language": {"en": "Language", "it": "Lingua"},
    "menu_help": {"en": "Help", "it": "Aiuto"},
    "menu_guide": {"en": "User guide", "it": "Guida"},
    "menu_about": {"en": "About Riot Office", "it": "Informazioni su Riot Office"},
    # --- status line ---
    "status_ok": {"en": "LibreOffice {version} ready", "it": "LibreOffice {version} pronto"},
    "status_missing": {
        "en": "LibreOffice not found: install it or run the Riot Office setup again",
        "it": "LibreOffice non trovato: installalo o esegui di nuovo il setup di Riot Office"},
    "status_no_config": {
        "en": "the Riot configuration is not installed (riot-office config install)",
        "it": "la configurazione Riot non è installata (riot-office config install)"},
    # --- dialogs ---
    "choose_pdfs": {"en": "Choose the PDFs to merge, in order", "it": "Scegli i PDF da unire, in ordine"},
    "choose_pdf": {"en": "Choose a PDF", "it": "Scegli un PDF"},
    "choose_documents": {"en": "Choose the documents to convert", "it": "Scegli i documenti da convertire"},
    "save_as": {"en": "Save as", "it": "Salva come"},
    "choose_folder": {"en": "Choose the destination folder", "it": "Scegli la cartella di destinazione"},
    "ask_pages": {
        "en": "Pages to rotate (for example 1,3-5; empty = all):",
        "it": "Pagine da ruotare (per esempio 1,3-5; vuoto = tutte):"},
    "ask_degrees": {"en": "Degrees clockwise (90, 180 or 270):", "it": "Gradi in senso orario (90, 180 o 270):"},
    "ask_ranges": {
        "en": "Page ranges, one file each (for example 1-3,4-10; empty = one file per page):",
        "it": "Intervalli di pagine, un file ciascuno (per esempio 1-3,4-10; vuoto = un file per pagina):"},
    "pdfa_question": {
        "en": "Save as PDF/A-2b, the archival format?",
        "it": "Salvare come PDF/A-2b, il formato per l'archiviazione?"},
    "done": {"en": "Done", "it": "Fatto"},
    "done_files": {"en": "{count} file(s) written in {folder}", "it": "{count} file scritti in {folder}"},
    "error": {"en": "Something went wrong", "it": "Qualcosa è andato storto"},
    "ocr_missing": {
        "en": "OCR needs OCRmyPDF and Tesseract (see the guide).",
        "it": "L'OCR richiede OCRmyPDF e Tesseract (vedi la guida)."},
    "language_changed": {
        "en": "LibreOffice will use English from the next start. Close any open LibreOffice window first.",
        "it": "LibreOffice userà l'italiano dal prossimo avvio. Chiudi prima le finestre di LibreOffice aperte."},
    "about": {
        "en": "Riot Office {version}\nA local office suite built on LibreOffice {lo}.\nMIT-0 licence for Riot Office's own files; "
              "LibreOffice is MPL-2.0 and belongs to The Document Foundation.",
        "it": "Riot Office {version}\nUna suite per ufficio locale basata su LibreOffice {lo}.\nLicenza MIT-0 per i file di "
              "Riot Office; LibreOffice è MPL-2.0 ed è di The Document Foundation."},
    "working": {"en": "Working{dots}", "it": "Al lavoro{dots}"},
}

_settings_cache: dict | None = None


def _load() -> dict:
    global _settings_cache
    if _settings_cache is None:
        try:
            _settings_cache = json.loads(SETTINGS.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _settings_cache = {}
    return _settings_cache


def system_language() -> str:
    """The interface language that matches the system's locale, English when none does."""
    candidates = [os.environ.get(v, "") for v in ("LC_ALL", "LC_MESSAGES", "LANG")]
    try:
        candidates.append(locale.getlocale()[0] or "")
    except ValueError:
        pass
    if sys.platform == "win32":
        try:
            import ctypes

            candidates.insert(0, locale.windows_locale.get(ctypes.windll.kernel32.GetUserDefaultUILanguage(), ""))
        except Exception:
            pass
    for value in candidates:
        code = value.lower()[:2]
        if code in LANGUAGES:
            return code
        if value.lower().startswith("italian"):
            return "it"
    return "en"


def get_language() -> str:
    """The saved interface language, or the system's one the first time."""
    code = _load().get("language")
    return code if code in LANGUAGES else system_language()


def set_language(code: str) -> None:
    """Remember ``code`` as the interface language."""
    if code not in LANGUAGES:
        raise ValueError(f"unknown language: {code}")
    settings = _load()
    settings["language"] = code
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS.write_text(json.dumps(settings, indent=1), encoding="utf-8")


def t(key: str, lang: str | None = None, **fields) -> str:
    """The text ``key`` in ``lang`` (default: the current language), with ``fields`` filled in."""
    texts = T[key]
    text = texts.get(lang or get_language()) or texts["en"]
    return text.format(dots=DOTS, **fields)
