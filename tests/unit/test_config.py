"""Unit tests for the config module."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class TestConfig:
    def test_default_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Clear all relevant env vars so defaults apply
        for key in [
            "LOG_LEVEL", "OUTPUT_DIR", "HEADING_FONT_SIZE_THRESHOLD",
            "CLEANER_PAGE_NUMBERS", "CLEANER_LINE_WRAP",
        ]:
            monkeypatch.delenv(key, raising=False)

        # Must re-import to bypass lru_cache
        import importlib
        import pdfcleanerx.config as cfg_mod
        importlib.reload(cfg_mod)

        cfg = cfg_mod.Config()
        assert cfg.heading_font_size_threshold == 1.2
        assert cfg.footer_repeat_threshold == 3
        assert cfg.cleaner_page_numbers is True

    def test_invalid_bool_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CLEANER_PAGE_NUMBERS", "maybe")

        import importlib
        import pdfcleanerx.config as cfg_mod
        importlib.reload(cfg_mod)

        from pdfcleanerx.exceptions import ConfigurationError
        with pytest.raises(ConfigurationError):
            cfg_mod._bool("CLEANER_PAGE_NUMBERS", True)

    def test_invalid_float_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import importlib
        import pdfcleanerx.config as cfg_mod
        importlib.reload(cfg_mod)

        from pdfcleanerx.exceptions import ConfigurationError
        monkeypatch.setenv("HEADING_FONT_SIZE_THRESHOLD", "not_a_float")
        with pytest.raises(ConfigurationError):
            cfg_mod._float("HEADING_FONT_SIZE_THRESHOLD", 1.2)
