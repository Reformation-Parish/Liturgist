"""Tests for liturgist.hymnal module."""

import base64
from pathlib import Path

import fitz  # pymupdf

from liturgist.hymnal import load_hymn_images, load_hymnal_sheets, parse_hymn_number

# Minimal valid 1x1 white PNG
TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
    b"\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00"
    b"\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _make_test_pdf(path: Path, num_pages: int = 1):
    """Create a minimal PDF with the given number of pages."""
    doc = fitz.open()
    for _ in range(num_pages):
        doc.new_page(width=72, height=72)
    doc.save(str(path))
    doc.close()


class TestParseHymnNumber:
    def test_standard_format(self):
        assert parse_hymn_number("Hymn 552 - Rejoice, All Ye Believers") == 552

    def test_single_digit(self):
        assert parse_hymn_number("Hymn 1 - A Mighty Fortress") == 1

    def test_case_insensitive(self):
        assert parse_hymn_number("hymn 100 - some title") == 100

    def test_no_title(self):
        assert parse_hymn_number("Hymn 42") == 42

    def test_no_match_plain_text(self):
        assert parse_hymn_number("Opening Prayer") is None

    def test_no_match_empty(self):
        assert parse_hymn_number("") is None

    def test_no_match_number_only(self):
        assert parse_hymn_number("552") is None


class TestLoadHymnImages:
    def test_single_page(self, tmp_path):
        (tmp_path / "100.png").write_bytes(TINY_PNG)
        result = load_hymn_images(100, tmp_path)
        assert len(result) == 1
        assert result[0].startswith("data:image/png;base64,")
        # Verify round-trip
        b64_data = result[0].removeprefix("data:image/png;base64,")
        assert base64.b64decode(b64_data) == TINY_PNG

    def test_multi_page(self, tmp_path):
        (tmp_path / "552-1.png").write_bytes(TINY_PNG)
        (tmp_path / "552-2.png").write_bytes(TINY_PNG)
        (tmp_path / "552-3.png").write_bytes(TINY_PNG)
        result = load_hymn_images(552, tmp_path)
        assert len(result) == 3
        for uri in result:
            assert uri.startswith("data:image/png;base64,")

    def test_multi_page_preferred_over_single(self, tmp_path):
        """When both 552-1.png and 552.png exist, multi-page wins."""
        (tmp_path / "552.png").write_bytes(TINY_PNG)
        (tmp_path / "552-1.png").write_bytes(TINY_PNG)
        (tmp_path / "552-2.png").write_bytes(TINY_PNG)
        result = load_hymn_images(552, tmp_path)
        assert len(result) == 2

    def test_missing(self, tmp_path):
        result = load_hymn_images(999, tmp_path)
        assert result == []

    def test_single_page_pdf(self, tmp_path):
        _make_test_pdf(tmp_path / "100.pdf", num_pages=1)
        result = load_hymn_images(100, tmp_path)
        assert len(result) == 1
        assert result[0].startswith("data:image/png;base64,")

    def test_multi_page_pdf(self, tmp_path):
        _make_test_pdf(tmp_path / "552.pdf", num_pages=3)
        result = load_hymn_images(552, tmp_path)
        assert len(result) == 3
        for uri in result:
            assert uri.startswith("data:image/png;base64,")

    def test_pdf_preferred_over_png(self, tmp_path):
        """When both 552.pdf and 552.png exist, PDF wins."""
        _make_test_pdf(tmp_path / "552.pdf", num_pages=2)
        (tmp_path / "552.png").write_bytes(TINY_PNG)
        result = load_hymn_images(552, tmp_path)
        assert len(result) == 2  # PDF has 2 pages, PNG would give 1

    def test_pdf_preferred_over_multi_png(self, tmp_path):
        """When both 552.pdf and 552-*.png exist, PDF wins."""
        _make_test_pdf(tmp_path / "552.pdf", num_pages=1)
        (tmp_path / "552-1.png").write_bytes(TINY_PNG)
        (tmp_path / "552-2.png").write_bytes(TINY_PNG)
        result = load_hymn_images(552, tmp_path)
        assert len(result) == 1  # PDF has 1 page, PNGs would give 2


class TestLoadHymnalSheets:
    def test_list_input(self, tmp_path):
        (tmp_path / "552.png").write_bytes(TINY_PNG)
        hymns = [
            "Hymn 552 - Rejoice, All Ye Believers",
            "Hymn 999 - Does Not Exist",
        ]
        result = load_hymnal_sheets(hymns, tmp_path)
        assert len(result) == 2
        assert len(result[0]) == 1
        assert result[1] == []

    def test_string_input(self, tmp_path):
        (tmp_path / "100.png").write_bytes(TINY_PNG)
        result = load_hymnal_sheets("Hymn 100 - A Title", tmp_path)
        assert len(result) == 1
        assert len(result[0]) == 1

    def test_no_hymn_number(self, tmp_path):
        result = load_hymnal_sheets("Doxology", tmp_path)
        assert result == [[]]

    def test_empty_list(self, tmp_path):
        result = load_hymnal_sheets([], tmp_path)
        assert result == []
