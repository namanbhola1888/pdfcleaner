"""Unit tests for the extractor layer."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from pdfcleanerx.exceptions import ExtractionError
from pdfcleanerx.extractor.pdfplumber_extractor import PdfPlumberExtractor


class TestPdfPlumberExtractor:
    def test_raises_for_missing_file(self, tmp_path: Path) -> None:
        extractor = PdfPlumberExtractor()
        with pytest.raises(ExtractionError, match="not found"):
            extractor.extract(tmp_path / "nonexistent.pdf")

    def test_raises_for_wrong_extension(self, tmp_path: Path) -> None:
        f = tmp_path / "file.txt"
        f.write_text("not a pdf")
        extractor = PdfPlumberExtractor()
        with pytest.raises(ExtractionError, match="Expected a .pdf file"):
            extractor.extract(f)

    def test_extracts_real_pdf(self, sample_pdf: Path) -> None:
        extractor = PdfPlumberExtractor()
        doc = extractor.extract(sample_pdf)
        assert len(doc.pages) >= 1
        assert doc.source_path == str(sample_pdf)

    def test_all_blocks_have_page_num(self, sample_pdf: Path) -> None:
        extractor = PdfPlumberExtractor()
        doc = extractor.extract(sample_pdf)
        for block in doc.all_blocks:
            assert block.page_num >= 1

    def test_corrupt_pdf_raises_extraction_error(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.pdf"
        bad.write_bytes(b"not a real pdf content at all")
        extractor = PdfPlumberExtractor()
        with pytest.raises(ExtractionError):
            extractor.extract(bad)
