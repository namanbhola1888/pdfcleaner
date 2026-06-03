"""Markdown formatter.

Converts a cleaned Document into a Markdown string.

Rules
-----
- Heading blocks (``_heading_level`` 1-3) → ``#``, ``##``, ``###``
- Image placeholder blocks → ``![image]``
- All other blocks → plain paragraph text
- Pages are separated by a blank line (no hard page-break marker by default)
- Consecutive blank lines are collapsed to one
"""

from __future__ import annotations

import logging
import re

from pdfcleanerx.exceptions import FormattingError
from pdfcleanerx.formatter.base import BaseFormatter
from pdfcleanerx.models import Document, TextBlock

logger = logging.getLogger(__name__)

_RE_IMAGE_PLACEHOLDER = re.compile(r"^\[image\]$", re.IGNORECASE)
_HEADING_PREFIX = {1: "#", 2: "##", 3: "###"}


class MarkdownFormatter(BaseFormatter):
    """Render a Document as GitHub-flavoured Markdown."""

    def format(self, document: Document) -> str:  # noqa: A003
        if not document.pages:
            raise FormattingError(
                "Cannot format an empty document.",
                hint="Ensure the PDF contains extractable text.",
            )

        lines: list[str] = []
        for page in document.pages:
            for block in page.blocks:
                rendered = self._render_block(block)
                if rendered is not None:
                    lines.append(rendered)
            # Blank line between pages (soft separator)
            lines.append("")

        result = "\n".join(lines)
        result = self._collapse_blank_lines(result)
        logger.debug("Formatted %d characters of Markdown", len(result))
        return result.strip() + "\n"

    # ── helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _render_block(block: TextBlock) -> str | None:
        text = block.text.strip()
        if not text:
            return None

        if _RE_IMAGE_PLACEHOLDER.match(text):
            return "\n![image]()\n"

        heading_level: int = getattr(block, "_heading_level", 0)
        if heading_level:
            prefix = _HEADING_PREFIX.get(heading_level, "###")
            return f"\n{prefix} {text}\n"

        return text

    @staticmethod
    def _collapse_blank_lines(text: str) -> str:
        """Replace 3+ consecutive newlines with exactly two (one blank line)."""
        return re.sub(r"\n{3,}", "\n\n", text)
