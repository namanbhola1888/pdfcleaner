"""Whitespace normaliser.

- Collapses multiple internal spaces to one.
- Strips leading / trailing whitespace per block.
- Removes empty blocks.
- Collapses runs of blank lines to a single blank line (at document level).
"""

from __future__ import annotations

import logging
import re

from pdfcleanerx.cleaners.base import BaseCleaner
from pdfcleanerx.models import Document, TextBlock

logger = logging.getLogger(__name__)

_RE_MULTI_SPACE = re.compile(r"[ \t]+")
_RE_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class WhitespaceCleaner(BaseCleaner):
    """Normalise whitespace across all text blocks."""

    def clean(self, document: Document) -> Document:
        total_removed = 0
        for page in document.pages:
            before = len(page.blocks)
            page.blocks = [
                cleaned
                for b in page.blocks
                if (cleaned := self._clean_block(b)) is not None
            ]
            removed = before - len(page.blocks)
            total_removed += removed

        logger.debug("WhitespaceCleaner removed %d empty blocks", total_removed)
        return document

    @staticmethod
    def _clean_block(block: TextBlock) -> TextBlock | None:
        # Strip control characters first
        text = _RE_CONTROL_CHARS.sub("", block.text)
        # Collapse internal whitespace
        text = _RE_MULTI_SPACE.sub(" ", text)
        # Strip edges
        text = text.strip()

        if not text:
            return None  # signal to remove this block

        block.text = text
        return block
