"""Shared data models passed between extractor, cleaners, and formatter."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TextBlock:
    """A single block of text extracted from a PDF page.

    Attributes
    ----------
    text:       Raw text content of the block.
    font_size:  Font size in points (None when unavailable).
    font_name:  Font name string (None when unavailable).
    is_bold:    Whether the block uses a bold font variant.
    page_num:   1-based page number the block belongs to.
    x0, y0:     Top-left bounding-box coordinates (points).
    x1, y1:     Bottom-right bounding-box coordinates (points).
    """

    text: str
    font_size: float | None = None
    font_name: str | None = None
    is_bold: bool = False
    page_num: int = 1
    x0: float = 0.0
    y0: float = 0.0
    x1: float = 0.0
    y1: float = 0.0


@dataclass
class PageData:
    """All text blocks extracted from a single PDF page.

    Attributes
    ----------
    page_num:   1-based page number.
    blocks:     Ordered list of TextBlock objects for the page.
    width:      Page width in points.
    height:     Page height in points.
    """

    page_num: int
    blocks: list[TextBlock] = field(default_factory=list)
    width: float = 0.0
    height: float = 0.0

    @property
    def full_text(self) -> str:
        """Concatenate all block texts with newlines."""
        return "\n".join(b.text for b in self.blocks if b.text.strip())


@dataclass
class Document:
    """Full extracted document, composed of ordered PageData objects."""

    pages: list[PageData] = field(default_factory=list)
    source_path: str = ""

    @property
    def all_blocks(self) -> list[TextBlock]:
        """Flat list of all TextBlock objects across all pages."""
        return [block for page in self.pages for block in page.blocks]
