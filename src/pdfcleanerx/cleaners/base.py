"""Abstract base class for all text cleaners."""

from __future__ import annotations

from abc import ABC, abstractmethod

from pdfcleanerx.models import Document


class BaseCleaner(ABC):
    """Contract for every cleaner stage.

    Each cleaner receives a *Document*, mutates or replaces its blocks,
    and returns the (possibly modified) Document.  Cleaners must not
    raise unless something is genuinely unrecoverable.
    """

    @property
    def name(self) -> str:
        """Human-readable name used in log messages."""
        return self.__class__.__name__

    @abstractmethod
    def clean(self, document: Document) -> Document:
        """Process *document* and return the cleaned version.

        Parameters
        ----------
        document:
            The Document produced by the extractor (or previous cleaner).

        Returns
        -------
        Document
            The same object (mutated in-place) or a new Document.
        """
