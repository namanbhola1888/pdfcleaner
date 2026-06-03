"""Page-number cleaner.

Strips three classes of page-number artefacts:
1. Standalone digits on a line  (e.g. ``42``)
2. "Page N of M" patterns       (e.g. ``Page 3 of 10``)
3. Repeated footer/header text  (same text on ≥ threshold consecutive pages)
"""

from __future__ import annotations

import logging
import re
from collections import Counter

from pdfcleanerx.cleaners.base import BaseCleaner
from pdfcleanerx.config import Config, get_config
from pdfcleanerx.models import Document, PageData, TextBlock

logger = logging.getLogger(__name__)

# ── compiled patterns ──────────────────────────────────────────────────────
_RE_STANDALONE_NUM = re.compile(r"^\s*\d+\s*$")
_RE_PAGE_N_OF_M = re.compile(r"^\s*[Pp]age\s+\d+\s+of\s+\d+\s*$")
_RE_PAGE_DASH = re.compile(r"^\s*[-–—]\s*\d+\s*[-–—]\s*$")  # – 3 –


class PageNumberCleaner(BaseCleaner):
    """Remove page-number artefacts from all pages."""

    def __init__(self, config: Config | None = None) -> None:
        self._cfg = config or get_config()

    def clean(self, document: Document) -> Document:
        repeated_footers = self._find_repeated_footers(document)
        if repeated_footers:
            logger.debug("Detected repeated footers: %s", repeated_footers)

        for page in document.pages:
            page.blocks = [
                b for b in page.blocks if not self._should_strip(b, repeated_footers)
            ]

        return document

    # ── helpers ────────────────────────────────────────────────────────────

    def _should_strip(self, block: TextBlock, repeated_footers: set[str]) -> bool:
        stripped = block.text.strip()

        if self._cfg.page_number_strip_standalone:
            if _RE_STANDALONE_NUM.match(stripped) or _RE_PAGE_DASH.match(stripped):
                logger.debug("  Stripping standalone page number: %r", stripped)
                return True

        if self._cfg.page_number_strip_page_n_of_m:
            if _RE_PAGE_N_OF_M.match(stripped):
                logger.debug("  Stripping 'Page N of M': %r", stripped)
                return True

        if self._cfg.page_number_strip_repeated_footer:
            if stripped in repeated_footers:
                logger.debug("  Stripping repeated footer: %r", stripped)
                return True

        return False

    def _find_repeated_footers(self, document: Document) -> set[str]:
        """Return text strings that appear on ≥ threshold pages (footer heuristic)."""
        if not self._cfg.page_number_strip_repeated_footer:
            return set()

        # Collect the first and last block text of every page (typical footer positions)
        candidates: Counter[str] = Counter()
        for page in document.pages:
            if not page.blocks:
                continue
            for block in [page.blocks[0], page.blocks[-1]]:
                text = block.text.strip()
                if text and len(text) < 80:  # footers are short
                    candidates[text] += 1

        threshold = self._cfg.footer_repeat_threshold
        return {text for text, count in candidates.items() if count >= threshold}
