"""Unit tests for individual cleaner stages."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tests.conftest import make_block, make_document

from pdfcleanerx.cleaners.heading import HeadingDetector
from pdfcleanerx.cleaners.line_wrap import LineWrapCleaner
from pdfcleanerx.cleaners.page_number import PageNumberCleaner
from pdfcleanerx.cleaners.whitespace import WhitespaceCleaner
from pdfcleanerx.config import Config
from pdfcleanerx.models import Document, PageData, TextBlock


# ── helpers ────────────────────────────────────────────────────────────────

def default_config(**overrides: object) -> Config:
    return Config(**overrides)  # type: ignore[arg-type]


# ══ PageNumberCleaner ══════════════════════════════════════════════════════

class TestPageNumberCleaner:
    def test_strips_standalone_digit(self) -> None:
        doc = make_document(["Hello world", "42", "More text"])
        result = PageNumberCleaner(default_config()).clean(doc)
        texts = [b.text for b in result.pages[0].blocks]
        assert "42" not in texts

    def test_strips_page_n_of_m(self) -> None:
        doc = make_document(["Body", "Page 3 of 10"])
        result = PageNumberCleaner(default_config()).clean(doc)
        texts = [b.text for b in result.pages[0].blocks]
        assert "Page 3 of 10" not in texts

    def test_strips_dash_page_number(self) -> None:
        doc = make_document(["Body", "– 3 –"])
        result = PageNumberCleaner(default_config()).clean(doc)
        texts = [b.text for b in result.pages[0].blocks]
        assert "– 3 –" not in texts

    def test_keeps_non_page_number(self) -> None:
        doc = make_document(["The year 2024 was significant."])
        result = PageNumberCleaner(default_config()).clean(doc)
        assert result.pages[0].blocks[0].text == "The year 2024 was significant."

    def test_strips_repeated_footer(self) -> None:
        # Same footer on 3 pages
        pages = []
        for i in range(1, 4):
            blocks = [make_block("Body text", page_num=i), make_block("Company Footer", page_num=i)]
            pages.append(PageData(page_num=i, blocks=blocks))
        doc = Document(pages=pages)

        cfg = default_config(footer_repeat_threshold=3)
        result = PageNumberCleaner(cfg).clean(doc)

        for page in result.pages:
            texts = [b.text for b in page.blocks]
            assert "Company Footer" not in texts

    def test_respects_feature_flag(self) -> None:
        doc = make_document(["Body", "42"])
        cfg = default_config(page_number_strip_standalone=False)
        result = PageNumberCleaner(cfg).clean(doc)
        texts = [b.text for b in result.pages[0].blocks]
        assert "42" in texts


# ══ WhitespaceCleaner ══════════════════════════════════════════════════════

class TestWhitespaceCleaner:
    def test_collapses_internal_spaces(self) -> None:
        doc = make_document(["Hello   world"])
        result = WhitespaceCleaner().clean(doc)
        assert result.pages[0].blocks[0].text == "Hello world"

    def test_strips_leading_trailing(self) -> None:
        doc = make_document(["  padded  "])
        result = WhitespaceCleaner().clean(doc)
        assert result.pages[0].blocks[0].text == "padded"

    def test_removes_empty_blocks(self) -> None:
        doc = make_document(["Good text", "   ", "", "More text"])
        result = WhitespaceCleaner().clean(doc)
        texts = [b.text for b in result.pages[0].blocks]
        assert "" not in texts
        assert "   " not in texts
        assert len(texts) == 2

    def test_removes_control_characters(self) -> None:
        doc = make_document(["Hello\x00World"])
        result = WhitespaceCleaner().clean(doc)
        assert result.pages[0].blocks[0].text == "HelloWorld"


# ══ LineWrapCleaner ════════════════════════════════════════════════════════

class TestLineWrapCleaner:
    def _make_doc(self, lines: list[str]) -> Document:
        blocks = [make_block(l) for l in lines]
        page = PageData(page_num=1, blocks=blocks)
        return Document(pages=[page])

    def test_merges_soft_wrapped_line(self) -> None:
        doc = self._make_doc(["This line continues", "on the next."])
        # "continues" doesn't end with terminal punct, "on" starts lowercase
        result = LineWrapCleaner().clean(doc)
        assert result.pages[0].blocks[0].text == "This line continues on the next."

    def test_does_not_merge_complete_sentence(self) -> None:
        doc = self._make_doc(["This is complete.", "Next sentence."])
        result = LineWrapCleaner().clean(doc)
        assert len(result.pages[0].blocks) == 2

    def test_does_not_merge_when_next_starts_uppercase(self) -> None:
        doc = self._make_doc(["First fragment", "Second Fragment"])
        result = LineWrapCleaner().clean(doc)
        assert len(result.pages[0].blocks) == 2

    def test_does_not_merge_headings(self) -> None:
        b1 = make_block("Introduction")
        b1._heading_level = 1  # type: ignore[attr-defined]
        b1._is_heading = True  # type: ignore[attr-defined]
        b2 = make_block("body text continues")
        page = PageData(page_num=1, blocks=[b1, b2])
        doc = Document(pages=[page])
        result = LineWrapCleaner().clean(doc)
        assert result.pages[0].blocks[0].text == "Introduction"
        assert result.pages[0].blocks[1].text == "body text continues"


# ══ HeadingDetector ════════════════════════════════════════════════════════

class TestHeadingDetector:
    def test_detects_large_font_heading(self) -> None:
        blocks = [
            make_block("BIG TITLE", font_size=24.0),
            make_block("Normal text here.", font_size=12.0),
            make_block("More body text.", font_size=12.0),
        ]
        page = PageData(page_num=1, blocks=blocks)
        doc = Document(pages=[page])

        HeadingDetector(default_config(heading_font_size_threshold=1.2)).clean(doc)

        assert getattr(blocks[0], "_heading_level", 0) in (1, 2, 3)
        assert getattr(blocks[1], "_heading_level", 0) == 0

    def test_detects_numbered_heading(self) -> None:
        blocks = [
            make_block("1. Introduction", font_size=12.0),
            make_block("Body text here.", font_size=12.0),
        ]
        page = PageData(page_num=1, blocks=blocks)
        doc = Document(pages=[page])

        HeadingDetector().clean(doc)

        assert getattr(blocks[0], "_heading_level", 0) == 2

    def test_detects_all_caps_heading(self) -> None:
        blocks = [make_block("CONCLUSION", font_size=12.0)]
        page = PageData(page_num=1, blocks=blocks)
        doc = Document(pages=[page])
        HeadingDetector().clean(doc)
        assert getattr(blocks[0], "_heading_level", 0) == 2

    def test_assigns_hierarchical_levels(self) -> None:
        # Use many body blocks at 11pt so the median is 11pt.
        # threshold=1.1 → cutoff = 12.1  →  14, 18, 24 all qualify; 11 does not.
        heading_blocks = [
            make_block("H1 title", font_size=24.0),
            make_block("H2 title", font_size=18.0),
            make_block("H3 title", font_size=14.0),
        ]
        body_blocks = [make_block(f"body line {i}", font_size=11.0) for i in range(9)]
        all_blocks = heading_blocks + body_blocks
        page = PageData(page_num=1, blocks=all_blocks)
        doc = Document(pages=[page])
        HeadingDetector(default_config(heading_font_size_threshold=1.1)).clean(doc)

        levels = [getattr(b, "_heading_level", 0) for b in heading_blocks]
        body_levels = [getattr(b, "_heading_level", 0) for b in body_blocks]
        assert levels[0] == 1
        assert levels[1] == 2
        assert levels[2] == 3
        assert all(lvl == 0 for lvl in body_levels)
