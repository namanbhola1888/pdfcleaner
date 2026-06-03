"""Public SDK entry point.

Typical usage::

    from pdfcleanerx import Converter

    # Default (uses pdfplumber extractor + full pipeline + Markdown formatter)
    converter = Converter()
    markdown: str = converter.convert("report.pdf")
    converter.convert_to_file("report.pdf", "report.md")

    # Custom pipeline (dependency injection)
    from pdfcleanerx.cleaners import CleanerPipeline, WhitespaceCleaner
    converter = Converter(pipeline=CleanerPipeline([WhitespaceCleaner()]))
"""

from __future__ import annotations

import logging
from pathlib import Path

from pdfcleanerx.cleaners import (
    CleanerPipeline,
    HeadingDetector,
    LineWrapCleaner,
    PageNumberCleaner,
    WhitespaceCleaner,
)
from pdfcleanerx.cleaners.base import BaseCleaner
from pdfcleanerx.config import Config, get_config
from pdfcleanerx.exceptions import OutputError
from pdfcleanerx.extractor import BaseExtractor, PdfPlumberExtractor
from pdfcleanerx.formatter import BaseFormatter, MarkdownFormatter

logger = logging.getLogger(__name__)


def _build_default_pipeline(cfg: Config) -> CleanerPipeline:
    """Construct the default cleaner pipeline respecting feature flags."""
    cleaners: list[BaseCleaner] = []

    if cfg.cleaner_page_numbers:
        cleaners.append(PageNumberCleaner(cfg))
    if cfg.cleaner_whitespace:
        cleaners.append(WhitespaceCleaner())
    if cfg.cleaner_headings:
        cleaners.append(HeadingDetector(cfg))
    if cfg.cleaner_line_wrap:
        # Line wrap runs *after* heading detection so it can skip heading blocks
        cleaners.append(LineWrapCleaner(cfg))

    return CleanerPipeline(cleaners)


class Converter:
    """Orchestrates extraction → cleaning → formatting.

    Parameters
    ----------
    extractor:
        A BaseExtractor implementation.  Defaults to PdfPlumberExtractor.
    pipeline:
        A CleanerPipeline.  Defaults to the full pipeline per config flags.
    formatter:
        A BaseFormatter implementation.  Defaults to MarkdownFormatter.
    config:
        Config instance.  Defaults to the singleton from get_config().
    """

    def __init__(
        self,
        extractor: BaseExtractor | None = None,
        pipeline: CleanerPipeline | None = None,
        formatter: BaseFormatter | None = None,
        config: Config | None = None,
    ) -> None:
        self._cfg = config or get_config()
        self._extractor = extractor or PdfPlumberExtractor()
        self._pipeline = pipeline or _build_default_pipeline(self._cfg)
        self._formatter = formatter or MarkdownFormatter()

        logger.debug(
            "Converter initialised | extractor=%s pipeline=%s formatter=%s",
            type(self._extractor).__name__,
            self._pipeline.cleaner_names,
            type(self._formatter).__name__,
        )

    def convert(self, pdf_path: str | Path) -> str:
        """Convert *pdf_path* to a Markdown string.

        Parameters
        ----------
        pdf_path:
            Path to the input PDF.

        Returns
        -------
        str
            Clean Markdown content.
        """
        path = Path(pdf_path)
        logger.info("Converting: %s", path)

        document = self._extractor.extract(path)
        document = self._pipeline.run(document)
        result = self._formatter.format(document)

        logger.info("Done: %d chars of Markdown produced", len(result))
        return result

    def convert_to_file(
        self,
        pdf_path: str | Path,
        output_path: str | Path | None = None,
    ) -> Path:
        """Convert *pdf_path* and write Markdown to *output_path*.

        If *output_path* is omitted the file is written to
        ``config.output_dir / <stem>.md``.

        Returns
        -------
        Path
            Absolute path of the written Markdown file.
        """
        pdf_path = Path(pdf_path)

        if output_path is None:
            out_dir = self._cfg.output_dir
            out_dir.mkdir(parents=True, exist_ok=True)
            output_path = out_dir / (pdf_path.stem + ".md")

        output_path = Path(output_path)

        markdown = self.convert(pdf_path)
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(markdown, encoding="utf-8")
        except OSError as exc:
            raise OutputError(
                f"Could not write output file '{output_path}': {exc}",
                hint="Check directory permissions.",
            ) from exc

        logger.info("Written: %s", output_path.resolve())
        return output_path.resolve()
