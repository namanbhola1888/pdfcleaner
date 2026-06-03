"""Unit tests for the Markdown formatter."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tests.conftest import make_block, make_document

from pdfcleanerx.exceptions import FormattingError
from pdfcleanerx.formatter.markdown import MarkdownFormatter
from pdfcleanerx.models import Document, PageData


class TestMarkdownFormatter:
    def _fmt(self) -> MarkdownFormatter:
        return MarkdownFormatter()

    def test_plain_body_text(self) -> None:
        doc = make_document(["Hello world"])
        result = self._fmt().format(doc)
        assert "Hello world" in result

    def test_h1_heading(self) -> None:
        doc = make_document(["Title"])
        doc.pages[0].blocks[0]._heading_level = 1  # type: ignore[attr-defined]
        result = self._fmt().format(doc)
        assert "# Title" in result

    def test_h2_heading(self) -> None:
        doc = make_document(["Section"])
        doc.pages[0].blocks[0]._heading_level = 2  # type: ignore[attr-defined]
        result = self._fmt().format(doc)
        assert "## Section" in result

    def test_h3_heading(self) -> None:
        doc = make_document(["Subsection"])
        doc.pages[0].blocks[0]._heading_level = 3  # type: ignore[attr-defined]
        result = self._fmt().format(doc)
        assert "### Subsection" in result

    def test_image_placeholder(self) -> None:
        doc = make_document(["[image]"])
        result = self._fmt().format(doc)
        assert "![image]()" in result

    def test_empty_document_raises(self) -> None:
        doc = Document(pages=[])
        with pytest.raises(FormattingError):
            self._fmt().format(doc)

    def test_no_triple_blank_lines(self) -> None:
        doc = make_document(["Para 1"], ["Para 2"], ["Para 3"])
        result = self._fmt().format(doc)
        assert "\n\n\n" not in result

    def test_ends_with_newline(self) -> None:
        doc = make_document(["Some text"])
        result = self._fmt().format(doc)
        assert result.endswith("\n")
