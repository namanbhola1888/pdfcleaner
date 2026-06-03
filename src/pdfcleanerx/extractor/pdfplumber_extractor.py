"""pdfplumber-based PDF extractor.

Extracts per-word font metadata to enable font-size heading detection
downstream.  Falls back gracefully when metadata is absent.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pdfplumber
from pdfplumber.page import Page

from pdfcleanerx.exceptions import ExtractionError
from pdfcleanerx.extractor.base import BaseExtractor
from pdfcleanerx.models import Document, PageData, TextBlock

logger = logging.getLogger(__name__)


class PdfPlumberExtractor(BaseExtractor):
    """Extract text and font metadata using pdfplumber."""

    # pdfplumber word-dict keys we care about
    _WORD_KEYS = ("text", "x0", "top", "x1", "bottom", "fontname", "size")

    def extract(self, pdf_path: Path) -> Document:
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise ExtractionError(
                f"PDF file not found: {pdf_path}",
                hint="Check the path and try again.",
            )
        if pdf_path.suffix.lower() != ".pdf":
            raise ExtractionError(
                f"Expected a .pdf file, got: {pdf_path.suffix!r}",
                hint="Only PDF files are supported.",
            )

        logger.info("Extracting: %s", pdf_path)

        try:
            with pdfplumber.open(pdf_path) as pdf:
                pages: list[PageData] = []
                for i, page in enumerate(pdf.pages, start=1):
                    page_data = self._extract_page(page, i)
                    pages.append(page_data)
                    logger.debug("  Page %d: %d blocks", i, len(page_data.blocks))
        except ExtractionError:
            raise
        except Exception as exc:
            raise ExtractionError(
                f"Failed to read PDF '{pdf_path}': {exc}",
                hint="The file may be encrypted, corrupted, or not a valid PDF.",
            ) from exc

        logger.info("Extraction complete: %d pages", len(pages))
        return Document(pages=pages, source_path=str(pdf_path))

    # ── private helpers ────────────────────────────────────────────────────

    def _extract_page(self, page: Page, page_num: int) -> PageData:
        """Convert a pdfplumber Page into a PageData of line-level TextBlocks."""
        page_data = PageData(
            page_num=page_num,
            width=float(page.width),
            height=float(page.height),
        )

        # Extract word-level dicts (includes font metadata).
        words = page.extract_words(
            extra_attrs=["fontname", "size"],
            keep_blank_chars=False,
            use_text_flow=True,
        )

        if not words:
            # Fallback: plain text, no font metadata
            raw = page.extract_text() or ""
            for line in raw.splitlines():
                if line.strip():
                    page_data.blocks.append(
                        TextBlock(text=line.strip(), page_num=page_num)
                    )
            return page_data

        # Group words into lines by their vertical position (top coordinate).
        lines = self._group_words_into_lines(words, page_num)
        page_data.blocks.extend(lines)
        return page_data

    @staticmethod
    def _group_words_into_lines(
        words: list[dict],  # type: ignore[type-arg]
        page_num: int,
        y_tolerance: float = 3.0,
    ) -> list[TextBlock]:
        """Group word dicts into line-level TextBlock objects.

        Words whose ``top`` values are within *y_tolerance* points are
        considered part of the same line.
        """
        if not words:
            return []

        lines: list[TextBlock] = []
        current_words: list[dict] = [words[0]]  # type: ignore[type-arg]

        for word in words[1:]:
            prev_top = current_words[-1].get("top", 0)
            curr_top = word.get("top", 0)
            if abs(curr_top - prev_top) <= y_tolerance:
                current_words.append(word)
            else:
                lines.append(
                    PdfPlumberExtractor._words_to_block(current_words, page_num)
                )
                current_words = [word]

        lines.append(PdfPlumberExtractor._words_to_block(current_words, page_num))
        return lines

    @staticmethod
    def _words_to_block(
        words: list[dict],  # type: ignore[type-arg]
        page_num: int,
    ) -> TextBlock:
        """Merge a list of word dicts into a single TextBlock."""
        text = " ".join(str(w.get("text", "")) for w in words)

        # Use the largest font size on the line as representative.
        sizes = [w.get("size") for w in words if w.get("size") is not None]
        font_size = max(sizes) if sizes else None

        # Predominant font name (first word's font is a reasonable proxy).
        font_name: str | None = words[0].get("fontname") if words else None
        is_bold = bool(font_name and "bold" in font_name.lower())

        x0 = float(words[0].get("x0", 0))
        y0 = float(words[0].get("top", 0))
        x1 = float(words[-1].get("x1", 0))
        y1 = float(words[-1].get("bottom", 0))

        return TextBlock(
            text=text,
            font_size=font_size,
            font_name=font_name,
            is_bold=is_bold,
            page_num=page_num,
            x0=x0,
            y0=y0,
            x1=x1,
            y1=y1,
        )
