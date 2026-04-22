"""
Hymnal sheet music loading for liturgist.

Loads hymn sheet music from a directory of PDFs or PNGs indexed by hymn number
and converts them to base64 data URIs for embedding in templates.
"""

import base64
import re
from pathlib import Path

import fitz  # pymupdf


def _png_data_uri(png_bytes: bytes) -> str:
    """Encode raw PNG bytes as a base64 data URI."""
    b64 = base64.b64encode(png_bytes).decode("ascii")
    return f"data:image/png;base64,{b64}"


def parse_hymn_number(hymn_string: str) -> int | None:
    """Extract hymn number from a string like 'Hymn 552 - Rejoice, All Ye Believers'."""
    match = re.search(r"Hymn\s+(\d+)", hymn_string, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def _rasterize_pdf(pdf_path: Path, dpi: int = 300) -> list[str]:
    """Rasterize each page of a PDF to a base64 PNG data URI."""
    pages = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            pixmap = page.get_pixmap(dpi=dpi)
            png_bytes = pixmap.tobytes("png")
            pages.append(_png_data_uri(png_bytes))
    return pages


def load_hymn_images(hymn_number: int, hymnal_dir: Path) -> list[str]:
    """Load images for a hymn number as base64 data URIs.

    Checks for files in this order:
    1. PDF: {num}.pdf (single or multi-page)
    2. Multi-page PNGs: {num}-1.png, {num}-2.png, ...
    3. Single PNG: {num}.png

    Returns a list of data URIs, or an empty list if no files found.
    """
    # 1. Check for PDF
    pdf_path = hymnal_dir / f"{hymn_number}.pdf"
    if pdf_path.is_file():
        return _rasterize_pdf(pdf_path)

    # 2. Check for multi-page PNGs
    first_page = hymnal_dir / f"{hymn_number}-1.png"
    if first_page.is_file():
        pages = []
        page_num = 1
        while True:
            page_path = hymnal_dir / f"{hymn_number}-{page_num}.png"
            if not page_path.is_file():
                break
            pages.append(_png_data_uri(page_path.read_bytes()))
            page_num += 1
        return pages

    # 3. Fall back to single PNG
    single_page = hymnal_dir / f"{hymn_number}.png"
    if single_page.is_file():
        return [_png_data_uri(single_page.read_bytes())]

    return []


def load_hymnal_sheets(hymns: str | list[str], hymnal_dir: Path) -> list[list[str]]:
    """Load sheet music for a list of hymns.

    Args:
        hymns: Single hymn string or list of hymn strings
              (e.g., "Hymn 552 - Rejoice, All Ye Believers")
        hymnal_dir: Directory containing PDFs or PNGs named by hymn number

    Returns:
        List parallel to hymns, each entry a list of base64 data URIs.
        Empty list for hymns with no matching files.
    """
    if isinstance(hymns, str):
        hymns = [hymns]

    sheets = []
    for hymn_str in hymns:
        number = parse_hymn_number(hymn_str)
        if number is not None:
            sheets.append(load_hymn_images(number, hymnal_dir))
        else:
            sheets.append([])
    return sheets
