"""Centralized configuration for pdfcleanerx.

All runtime values come from environment variables (populated via .env).
Changing a value requires editing only the .env file – nothing else.

Usage::

    from pdfcleanerx.config import get_config

    cfg = get_config()          # cached singleton
    print(cfg.log_level)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

from pdfcleanerx.exceptions import ConfigurationError

# Load .env from cwd (or parent dirs) once at import time.
load_dotenv(override=False)


def _bool(key: str, default: bool) -> bool:
    val = os.getenv(key, str(default)).strip().lower()
    if val in ("1", "true", "yes"):
        return True
    if val in ("0", "false", "no"):
        return False
    raise ConfigurationError(
        f"Environment variable '{key}' must be a boolean (true/false), got: {val!r}"
    )


def _int(key: str, default: int) -> int:
    val = os.getenv(key, str(default)).strip()
    try:
        return int(val)
    except ValueError:
        raise ConfigurationError(
            f"Environment variable '{key}' must be an integer, got: {val!r}"
        )


def _float(key: str, default: float) -> float:
    val = os.getenv(key, str(default)).strip()
    try:
        return float(val)
    except ValueError:
        raise ConfigurationError(
            f"Environment variable '{key}' must be a float, got: {val!r}"
        )


def _log_level(key: str, default: str) -> int:
    raw = os.getenv(key, default).strip().upper()
    level = getattr(logging, raw, None)
    if not isinstance(level, int):
        raise ConfigurationError(
            f"Environment variable '{key}' must be a valid log level "
            f"(DEBUG/INFO/WARNING/ERROR/CRITICAL), got: {raw!r}"
        )
    return level


@dataclass(frozen=True)
class Config:
    # ── Logging ───────────────────────────────
    log_level: int = logging.INFO

    # ── Output ────────────────────────────────
    output_dir: Path = field(default_factory=lambda: Path("./output"))

    # ── Heading Detection ─────────────────────
    heading_font_size_threshold: float = 1.2
    heading_min_length: int = 3
    heading_max_length: int = 120

    # ── Line-Wrap Cleaner ─────────────────────
    line_terminal_punctuation: str = ".!?:;"

    # ── Page-Number Cleaner ───────────────────
    page_number_strip_standalone: bool = True
    page_number_strip_page_n_of_m: bool = True
    page_number_strip_repeated_footer: bool = True
    footer_repeat_threshold: int = 3

    # ── Pipeline Feature Flags ────────────────
    cleaner_page_numbers: bool = True
    cleaner_line_wrap: bool = True
    cleaner_whitespace: bool = True
    cleaner_headings: bool = True


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Return the cached singleton Config built from environment variables."""
    return Config(
        log_level=_log_level("LOG_LEVEL", "INFO"),
        output_dir=Path(os.getenv("OUTPUT_DIR", "./output")),
        heading_font_size_threshold=_float("HEADING_FONT_SIZE_THRESHOLD", 1.2),
        heading_min_length=_int("HEADING_MIN_LENGTH", 3),
        heading_max_length=_int("HEADING_MAX_LENGTH", 120),
        line_terminal_punctuation=os.getenv("LINE_TERMINAL_PUNCTUATION", ".!?:;"),
        page_number_strip_standalone=_bool("PAGE_NUMBER_STRIP_STANDALONE", True),
        page_number_strip_page_n_of_m=_bool("PAGE_NUMBER_STRIP_PAGE_N_OF_M", True),
        page_number_strip_repeated_footer=_bool(
            "PAGE_NUMBER_STRIP_REPEATED_FOOTER", True
        ),
        footer_repeat_threshold=_int("FOOTER_REPEAT_THRESHOLD", 3),
        cleaner_page_numbers=_bool("CLEANER_PAGE_NUMBERS", True),
        cleaner_line_wrap=_bool("CLEANER_LINE_WRAP", True),
        cleaner_whitespace=_bool("CLEANER_WHITESPACE", True),
        cleaner_headings=_bool("CLEANER_HEADINGS", True),
    )
