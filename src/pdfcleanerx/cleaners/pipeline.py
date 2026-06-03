"""Cleaner pipeline: runs an ordered list of BaseCleaner instances."""

from __future__ import annotations

import logging

from pdfcleanerx.cleaners.base import BaseCleaner
from pdfcleanerx.exceptions import CleaningError
from pdfcleanerx.models import Document

logger = logging.getLogger(__name__)


class CleanerPipeline:
    """Orchestrates an ordered sequence of cleaners.

    Parameters
    ----------
    cleaners:
        Ordered list of BaseCleaner instances.  Pass an empty list to
        skip all cleaning (useful in tests).
    """

    def __init__(self, cleaners: list[BaseCleaner]) -> None:
        self._cleaners = cleaners

    def run(self, document: Document) -> Document:
        """Run all cleaners in order, returning the final Document.

        Raises
        ------
        CleaningError
            If any cleaner raises an unexpected exception.
        """
        for cleaner in self._cleaners:
            logger.debug("Running cleaner: %s", cleaner.name)
            try:
                document = cleaner.clean(document)
            except CleaningError:
                raise
            except Exception as exc:
                raise CleaningError(
                    f"Cleaner '{cleaner.name}' raised an unexpected error: {exc}",
                    hint="Check your configuration or report this as a bug.",
                ) from exc
            logger.debug("  Done: %s", cleaner.name)

        return document

    @property
    def cleaner_names(self) -> list[str]:
        return [c.name for c in self._cleaners]
