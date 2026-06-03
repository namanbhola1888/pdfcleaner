"""Generate deterministic PDF fixtures used by the test suite.

Run once to (re-)create the fixture files::

    python tests/fixtures/generate_fixture.py

Requires reportlab (dev dependency only).
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

FIXTURES_DIR = Path(__file__).parent


def build_sample_pdf(path: Path) -> None:
    """Create a multi-page PDF with headings, body text, and page numbers."""
    doc = SimpleDocTemplate(str(path), pagesize=letter)
    styles = getSampleStyleSheet()

    heading1 = ParagraphStyle(
        "H1",
        parent=styles["Heading1"],
        fontSize=24,
        spaceAfter=12,
    )
    heading2 = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontSize=18,
        spaceAfter=8,
    )
    body = styles["Normal"]

    story = []

    # ── Page 1 ─────────────────────────────────────────────────────────────
    story.append(Paragraph("Introduction", heading1))
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "This is the first paragraph of the introduction. "
            "It contains normal body text that may wrap across lines "
            "when the PDF is rendered.",
            body,
        )
    )
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "A second paragraph follows. Whitespace   normalisation should "
            "collapse the extra spaces inside this sentence.",
            body,
        )
    )
    story.append(Spacer(1, 6))
    story.append(Paragraph("1", body))  # standalone page number

    story.append(PageBreak())

    # ── Page 2 ─────────────────────────────────────────────────────────────
    story.append(Paragraph("1. Background", heading2))
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "Section one covers the background. "
            "This sentence is intentionally long so that pdfplumber will "
            "extract it as multiple lines that the line-wrap cleaner should merge.",
            body,
        )
    )
    story.append(Spacer(1, 6))
    story.append(Paragraph("Page 2 of 3", body))  # Page N of M pattern

    story.append(PageBreak())

    # ── Page 3 ─────────────────────────────────────────────────────────────
    story.append(Paragraph("CONCLUSION", heading1))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Final remarks go here.", body))
    story.append(Spacer(1, 6))
    story.append(Paragraph("3", body))  # standalone page number

    doc.build(story)
    print(f"Created: {path}")


if __name__ == "__main__":
    build_sample_pdf(FIXTURES_DIR / "sample.pdf")
