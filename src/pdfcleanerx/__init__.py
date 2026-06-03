"""
pdfcleanerx – Convert messy PDF-extracted text into clean Markdown files.

Public API::

    from pdfcleanerx import Converter

    converter = Converter()
    markdown = converter.convert("report.pdf")
    converter.convert_to_file("report.pdf", "report.md")
"""

from pdfcleanerx.converter import Converter

__all__ = ["Converter"]
__version__ = "0.1.0"
