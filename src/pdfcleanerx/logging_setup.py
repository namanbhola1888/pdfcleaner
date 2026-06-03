"""Logging configuration for pdfcleanerx.

Call ``setup_logging()`` once at startup (CLI does this automatically).
Library users can call it too, or configure logging themselves.
"""

from __future__ import annotations

import logging
import sys

from rich.logging import RichHandler


def setup_logging(level: int = logging.INFO, *, rich: bool = True) -> None:
    """Configure root logger for pdfcleanerx.

    Parameters
    ----------
    level:
        Logging level (e.g. ``logging.DEBUG``).
    rich:
        Use Rich's colourful handler (True for CLI, False for library usage).
    """
    pkg_logger = logging.getLogger("pdfcleanerx")
    pkg_logger.setLevel(level)

    if pkg_logger.handlers:
        return  # already configured

    if rich:
        handler: logging.Handler = RichHandler(
            show_path=False,
            markup=True,
            rich_tracebacks=False,
        )
        fmt = "%(message)s"
    else:
        handler = logging.StreamHandler(sys.stderr)
        fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

    handler.setFormatter(logging.Formatter(fmt))
    pkg_logger.addHandler(handler)
    pkg_logger.propagate = False
