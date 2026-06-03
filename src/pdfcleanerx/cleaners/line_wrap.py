"""Line-wrap cleaner.

Merges lines that were soft-wrapped by the PDF renderer.
A line is merged into the next when:
  - It does not end with terminal punctuation (configurable set).
  - AND the next line starts with a lowercase letter.
  - AND neither line has been flagged as a heading.
"""

from __future__ import annotations

import logging

from pdfcleanerx.cleaners.base import BaseCleaner
from pdfcleanerx.config import Config, get_config
from pdfcleanerx.models import Document, PageData, TextBlock

logger = logging.getLogger(__name__)


class LineWrapCleaner(BaseCleaner):
    """Merge soft-wrapped lines within each page."""

    def __init__(self, config: Config | None = None) -> None:
        self._cfg = config or get_config()

    def clean(self, document: Document) -> Document:
        for page in document.pages:
            page.blocks = self._merge_blocks(page.blocks)
        return document

    def _merge_blocks(self, blocks: list[TextBlock]) -> list[TextBlock]:
        if not blocks:
            return blocks

        terminal = set(self._cfg.line_terminal_punctuation)
        merged: list[TextBlock] = []
        i = 0

        while i < len(blocks):
            current = blocks[i]

            # Keep merging while conditions hold
            while i + 1 < len(blocks):
                next_block = blocks[i + 1]
                if self._should_merge(current, next_block, terminal):
                    logger.debug(
                        "  Merging: %r + %r",
                        current.text[:40],
                        next_block.text[:40],
                    )
                    current = self._merge_two(current, next_block)
                    i += 1
                else:
                    break

            merged.append(current)
            i += 1

        return merged

    @staticmethod
    def _should_merge(
        current: TextBlock,
        nxt: TextBlock,
        terminal: set[str],
    ) -> bool:
        # Never merge heading-flagged blocks (set by HeadingDetector)
        if getattr(current, "_is_heading", False) or getattr(nxt, "_is_heading", False):
            return False

        curr_text = current.text.rstrip()
        if not curr_text:
            return False

        # Current line ends with terminal punctuation → it's a complete sentence
        if curr_text[-1] in terminal:
            return False

        next_text = nxt.text.lstrip()
        if not next_text:
            return False

        # Next line starts uppercase → likely a new sentence / heading
        if next_text[0].isupper():
            return False

        return True

    @staticmethod
    def _merge_two(a: TextBlock, b: TextBlock) -> TextBlock:
        """Combine two blocks, keeping metadata from the first."""
        return TextBlock(
            text=a.text.rstrip() + " " + b.text.lstrip(),
            font_size=a.font_size,
            font_name=a.font_name,
            is_bold=a.is_bold,
            page_num=a.page_num,
            x0=a.x0,
            y0=a.y0,
            x1=max(a.x1, b.x1),
            y1=max(a.y1, b.y1),
        )
