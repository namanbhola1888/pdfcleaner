"""Custom exceptions for pdfcleanerx.

Hierarchy
---------
PdfCleanerXError          (base)
├── ExtractionError       PDF could not be read / parsed
├── CleaningError         A cleaner stage failed
├── FormattingError       Formatter could not produce output
├── ConfigurationError    Invalid / missing configuration
└── OutputError           Could not write output file
"""


class PdfCleanerXError(Exception):
    """Base exception for all pdfcleanerx errors."""

    def __init__(self, message: str, *, hint: str | None = None) -> None:
        super().__init__(message)
        self.hint = hint

    def __str__(self) -> str:
        base = super().__str__()
        if self.hint:
            return f"{base}\n  Hint: {self.hint}"
        return base


class ExtractionError(PdfCleanerXError):
    """Raised when PDF text extraction fails."""


class CleaningError(PdfCleanerXError):
    """Raised when a cleaner stage raises an unexpected error."""


class FormattingError(PdfCleanerXError):
    """Raised when the formatter cannot produce output."""


class ConfigurationError(PdfCleanerXError):
    """Raised when configuration values are invalid or missing."""


class OutputError(PdfCleanerXError):
    """Raised when the output file cannot be written."""
