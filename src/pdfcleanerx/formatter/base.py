"""Abstract base class for output formatters."""

from __future__ import annotations

from abc import ABC, abstractmethod

from pdfcleanerx.models import Document


class BaseFormatter(ABC):
    """Contract for every output formatter.

    To add a new format (e.g. HTML, reStructuredText):
    1. Subclass BaseFormatter.
    2. Implement ``format()``.
    3. Inject the new class into Converter.
    """

    @abstractmethod
    def format(self, document: Document) -> str:
        """Convert *document* to a string in the target format.

        Parameters
        ----------
        document:
            The cleaned Document.

        Returns
        -------
        str
            Full output content ready to write to a file.

        Raises
        ------
        FormattingError
            If formatting fails for any reason.
        """
