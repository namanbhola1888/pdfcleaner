"""Heading detector.

Two-pass heuristic approach:
  Pass 1 – Font-size based: blocks whose font size exceeds
            (mean body font size × threshold) are heading candidates.
  Pass 2 – Pattern based: ALL-CAPS short lines, numbered sections
            (1., 1.1., Chapter N), and bold lines that look like headings.

Heading level is assigned by relative font size:
  largest  → H1, next tier → H2, rest → H3.
  Pattern-only headings (no font metadata) default to H2.

A private attribute ``_heading_level`` (int 1-3) is set on qualifying
TextBlock objects.  The formatter reads this attribute.
"""

from __future__ import annotations

import logging
import re
import statistics
from typing import NamedTuple

from pdfcleanerx.cleaners.base import BaseCleaner
from pdfcleanerx.config import Config, get_config
from pdfcleanerx.models import Document, TextBlock

logger = logging.getLogger(__name__)

# ── regex patterns ─────────────────────────────────────────────────────────
_RE_NUMBERED = re.compile(
    r"^(\d+\.){1,3}\s+\S"  # 1. / 1.1. / 1.1.1.
    r"|^(Chapter|Section|Part|Appendix)\s+\w+",  # Chapter 3
    re.IGNORECASE,
)
_RE_ALL_CAPS = re.compile(r"^[A-Z][A-Z0-9 \t,.:;!?'\-–—]{2,}$")


class _HeadingTier(NamedTuple):
    level: int          # 1, 2, or 3
    font_size: float    # representative size for this tier (0 = pattern-only)


class HeadingDetector(BaseCleaner):
    """Detect and tag heading blocks with a ``_heading_level`` attribute."""

    def __init__(self, config: Config | None = None) -> None:
        self._cfg = config or get_config()

    def clean(self, document: Document) -> Document:
        all_blocks = document.all_blocks
        body_font_size = self._estimate_body_font_size(all_blocks)
        logger.debug("Estimated body font size: %.1f pt", body_font_size)

        threshold = body_font_size * self._cfg.heading_font_size_threshold
        size_candidates: list[TextBlock] = []

        for block in all_blocks:
            if not self._text_length_ok(block.text):
                continue
            if block.font_size is not None and block.font_size >= threshold:
                size_candidates.append(block)
            elif self._matches_pattern(block.text):
                self._tag(block, level=2)

        # Assign hierarchical levels to font-size candidates
        self._assign_size_levels(size_candidates)

        # Mark _is_heading on all tagged blocks (used by LineWrapCleaner guard)
        for block in all_blocks:
            if getattr(block, "_heading_level", 0):
                object.__setattr__(block, "_is_heading", True) if hasattr(
                    block, "__slots__"
                ) else setattr(block, "_is_heading", True)

        return document

    # ── helpers ────────────────────────────────────────────────────────────

    def _text_length_ok(self, text: str) -> bool:
        n = len(text.strip())
        return self._cfg.heading_min_length <= n <= self._cfg.heading_max_length

    @staticmethod
    def _matches_pattern(text: str) -> bool:
        stripped = text.strip()
        return bool(_RE_NUMBERED.match(stripped) or _RE_ALL_CAPS.match(stripped))

    @staticmethod
    def _tag(block: TextBlock, level: int) -> None:
        block._heading_level = level  # type: ignore[attr-defined]
        block._is_heading = True      # type: ignore[attr-defined]

    @staticmethod
    def _estimate_body_font_size(blocks: list[TextBlock]) -> float:
        sizes = [b.font_size for b in blocks if b.font_size is not None]
        if not sizes:
            return 12.0  # sensible default
        try:
            return statistics.median(sizes)
        except statistics.StatisticsError:
            return sizes[0]

    def _assign_size_levels(self, candidates: list[TextBlock]) -> None:
        if not candidates:
            return

        # Collect unique sizes and sort descending
        unique_sizes = sorted(
            {b.font_size for b in candidates if b.font_size is not None},
            reverse=True,
        )

        # Map the top 3 distinct sizes to H1, H2, H3
        size_to_level: dict[float, int] = {}
        for i, size in enumerate(unique_sizes[:3]):
            size_to_level[size] = i + 1  # 1, 2, or 3

        for block in candidates:
            fs = block.font_size
            level = size_to_level.get(fs, 3) if fs is not None else 3
            self._tag(block, level=level)
            logger.debug(
                "  Heading H%d (%.1f pt): %r",
                level,
                fs or 0,
                block.text[:60],
            )
