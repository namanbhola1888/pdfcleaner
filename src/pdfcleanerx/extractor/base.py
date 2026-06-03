"""Abstract base class for PDF extractors.

To add a new extractor (e.g. OCR, pymupdf):
1. Subclass BaseExtractor.
2. Implement ``extract()``.
3. Inject the new class into Converter.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from pdfcleanerx.models import Document


class BaseExtractor(ABC):
    """Contract that every extractor must fulfil."""

    @abstractmethod
    def extract(self, pdf_path: Path) -> Document:
        """Extract text and metadata from *pdf_path*.

        Parameters
        ----------
        pdf_path:
            Absolute or relative path to the PDF file.

        Returns
        -------
        Document
            Populated Document containing ordered PageData objects.

        Raises
        ------
        ExtractionError
            If the file cannot be opened or parsed.
        """
