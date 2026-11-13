"""Fidelity check: how close LibreOffice's rendering of a document is to Microsoft Office's.

For every document in a corpus there must be a reference PDF with the same name, exported from
licensed Microsoft Office (File > Save as > PDF). LibreOffice converts the document to PDF headless
and the two PDFs are compared:

- page count (a different count is the most visible layout problem);
- text similarity (0-1, word sequence, insensitive to line breaks and spacing).

Pixel comparison (SSIM per page) is planned for a later release, see docs/ROADMAP.md.
"""

import difflib
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

from .libreoffice import EXTENSION_MODULE, Installation, convert

PAGE_TOLERANCE = 0
TEXT_THRESHOLD = 0.95


@dataclass
class Result:
    """The comparison of one document."""

    document: Path
    reference_pages: int | None = None
    riot_pages: int | None = None
    text_similarity: float | None = None
    error: str | None = None

    @property
    def passed(self) -> bool:
        return (self.error is None and self.reference_pages == self.riot_pages
                and (self.text_similarity or 0) >= TEXT_THRESHOLD)


def pdf_words(path: Path) -> list[str]:
    """Every word of a PDF, in reading order as extracted by pypdf."""
    text = " ".join(page.extract_text() or "" for page in PdfReader(path).pages)
    return re.findall(r"\w+", text.lower())


def similarity(a: list[str], b: list[str]) -> float:
    if not a and not b:
        return 1.0
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


def compare(inst: Installation, corpus: Path, references: Path, work_dir: Path | None = None) -> list[Result]:
    """Convert each document of ``corpus`` and compare it with ``references/<name>.pdf``."""
    results = []
    with tempfile.TemporaryDirectory(prefix="riot-fidelity-") as tmp:
        out_dir = work_dir or Path(tmp)
        for doc in sorted(p for p in corpus.rglob("*") if p.is_file() and p.suffix.lower().lstrip(".") in EXTENSION_MODULE):
            rel = doc.relative_to(corpus)
            result = Result(rel)
            reference = (references / rel).with_suffix(".pdf")
            try:
                if not reference.exists():
                    raise FileNotFoundError(f"no reference PDF {reference.name}")
                ours = convert(inst, [doc], out_dir / rel.parent)[0]
                result.reference_pages = len(PdfReader(reference).pages)
                result.riot_pages = len(PdfReader(ours).pages)
                result.text_similarity = similarity(pdf_words(reference), pdf_words(ours))
            except Exception as exc:  # one bad file must not stop the whole corpus
                result.error = str(exc)
            results.append(result)
    return results


def markdown(results: list[Result], corpus: Path) -> str:
    """A readable report: pass rate, then every document with its numbers."""
    compared = [r for r in results if r.error is None]
    passed = sum(r.passed for r in results)
    same_pages = sum(r.reference_pages == r.riot_pages for r in compared)
    mean = sum(r.text_similarity for r in compared) / len(compared) if compared else 0.0
    lines = [f"# Fidelity report of `{corpus}`", "",
             f"- Documents: **{len(results)}**, compared: {len(compared)}, errors: {len(results) - len(compared)}",
             f"- Same page count: **{same_pages}/{len(compared)}**",
             f"- Mean text similarity: **{mean:.3f}**",
             f"- Passed (same pages and similarity >= {TEXT_THRESHOLD}): **{passed}/{len(results)}**", "",
             "| Document | Pages (Office) | Pages (Riot) | Text | Result |", "|---|---:|---:|---:|---|"]
    for r in results:
        if r.error:
            lines.append(f"| `{r.document.as_posix()}` | | | | error: {r.error} |")
        else:
            lines.append(f"| `{r.document.as_posix()}` | {r.reference_pages} | {r.riot_pages} | "
                         f"{r.text_similarity:.3f} | {'pass' if r.passed else 'CHECK'} |")
    return "\n".join(lines) + "\n"
