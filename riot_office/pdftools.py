"""Everyday PDF operations: merge, split, rotate and OCR.

Merge, split and rotate are done in-process with pypdf (BSD licence). OCR calls OCRmyPDF with
Tesseract when they are installed. These are the first tools of Riot PDF; the full desktop editor
(viewer, annotations, forms, redaction, signatures) is planned on top of PDF4QT, see docs/ROADMAP.md.
"""

import shutil
import subprocess
from pathlib import Path

from pypdf import PdfReader, PdfWriter


def parse_pages(spec: str, count: int) -> list[int]:
    """Turn "1,3-5" into zero-based page indices; an empty spec means every page.

    Raises ValueError for pages outside 1..count or malformed ranges.
    """
    spec = spec.replace(" ", "")
    if not spec:
        return list(range(count))
    pages: list[int] = []
    for part in spec.split(","):
        first, sep, last = part.partition("-")
        start = int(first)
        end = int(last) if sep else start
        if not 1 <= start <= end <= count:
            raise ValueError(f"page range {part!r} is outside 1-{count}")
        pages.extend(range(start - 1, end))
    return pages


def parse_ranges(spec: str, count: int) -> list[tuple[int, int]]:
    """Turn "1-3,4-10" into one-based inclusive ranges; empty means one range per page."""
    spec = spec.replace(" ", "")
    if not spec:
        return [(p, p) for p in range(1, count + 1)]
    ranges = []
    for part in spec.split(","):
        first, sep, last = part.partition("-")
        start, end = int(first), int(last) if sep else int(first)
        if not 1 <= start <= end <= count:
            raise ValueError(f"page range {part!r} is outside 1-{count}")
        ranges.append((start, end))
    return ranges


def page_count(path: Path) -> int:
    return len(PdfReader(path).pages)


def merge(inputs: list[Path], output: Path) -> Path:
    """Write the pages of ``inputs``, in order, into ``output``; bookmarks get the file names."""
    if not inputs:
        raise ValueError("nothing to merge")
    writer = PdfWriter()
    for src in inputs:
        start = len(writer.pages)
        writer.append(str(src))
        writer.add_outline_item(src.stem, start)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "wb") as f:
        writer.write(f)
    return output


def split(src: Path, out_dir: Path, ranges: str = "") -> list[Path]:
    """Split ``src`` into one file per range ("1-3,4-10"), or one file per page by default."""
    reader = PdfReader(src)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for start, end in parse_ranges(ranges, len(reader.pages)):
        writer = PdfWriter()
        for index in range(start - 1, end):
            writer.add_page(reader.pages[index])
        suffix = f"p{start}" if start == end else f"p{start}-{end}"
        dest = out_dir / f"{src.stem}_{suffix}.pdf"
        with open(dest, "wb") as f:
            writer.write(f)
        written.append(dest)
    return written


def rotate(src: Path, output: Path, degrees: int, pages: str = "") -> Path:
    """Rotate the chosen pages (all by default) clockwise by 90, 180 or 270 degrees."""
    if degrees % 90 or degrees % 360 == 0:
        raise ValueError("degrees must be 90, 180 or 270")
    reader = PdfReader(src)
    chosen = set(parse_pages(pages, len(reader.pages)))
    writer = PdfWriter(clone_from=reader)
    for index, page in enumerate(writer.pages):
        if index in chosen:
            page.rotate(degrees)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "wb") as f:
        writer.write(f)
    return output


def ocr_available() -> bool:
    return bool(shutil.which("ocrmypdf") and shutil.which("tesseract"))


def ocr(src: Path, output: Path, languages: str = "ita+eng", pdfa: bool = True) -> Path:
    """Add a searchable text layer with OCRmyPDF; pages that already have text are left alone."""
    if not ocr_available():
        raise RuntimeError("OCRmyPDF and Tesseract are not installed")
    args = ["ocrmypdf", "-l", languages, "--skip-text", "--output-type", "pdfa" if pdfa else "pdf", str(src), str(output)]
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode not in (0, 6):  # 6: the file already had text, nothing to do
        raise RuntimeError(result.stderr.strip() or f"ocrmypdf exited with {result.returncode}")
    if result.returncode == 6 and not output.exists():
        shutil.copyfile(src, output)
    return output
