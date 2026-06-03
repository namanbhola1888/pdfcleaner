"""Integration tests: full pipeline from PDF to Markdown."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from pdfcleanerx.converter import Converter
from pdfcleanerx.exceptions import ExtractionError, OutputError


class TestConverterIntegration:
    def test_convert_returns_markdown_string(self, sample_pdf: Path) -> None:
        converter = Converter()
        result = converter.convert(sample_pdf)
        assert isinstance(result, str)
        assert len(result) > 0
        assert result.endswith("\n")

    def test_convert_produces_no_triple_blank_lines(self, sample_pdf: Path) -> None:
        converter = Converter()
        result = converter.convert(sample_pdf)
        assert "\n\n\n" not in result

    def test_convert_detects_headings(self, sample_pdf: Path) -> None:
        converter = Converter()
        result = converter.convert(sample_pdf)
        # sample PDF has "Introduction" (H1 size), should appear as heading
        assert "#" in result

    def test_page_numbers_stripped(self, sample_pdf: Path) -> None:
        converter = Converter()
        result = converter.convert(sample_pdf)
        lines = result.splitlines()
        # Standalone digits should not appear as their own line
        standalone_digits = [l for l in lines if l.strip().isdigit()]
        assert standalone_digits == []

    def test_page_n_of_m_stripped(self, sample_pdf: Path) -> None:
        converter = Converter()
        result = converter.convert(sample_pdf)
        import re
        assert not re.search(r"^Page \d+ of \d+$", result, re.MULTILINE)

    def test_convert_to_file_writes_md(
        self, sample_pdf: Path, tmp_path: Path
    ) -> None:
        out = tmp_path / "output.md"
        converter = Converter()
        written = converter.convert_to_file(sample_pdf, out)
        assert written == out.resolve()
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert len(content) > 0

    def test_convert_to_file_default_dir(
        self, sample_pdf: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        import importlib
        import pdfcleanerx.config as cfg_mod
        cfg_mod.get_config.cache_clear()  # type: ignore[attr-defined]
        monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "out"))
        cfg_mod.get_config.cache_clear()  # type: ignore[attr-defined]

        converter = Converter()
        written = converter.convert_to_file(sample_pdf)
        assert written.suffix == ".md"
        assert written.exists()

    def test_missing_pdf_raises(self, tmp_path: Path) -> None:
        converter = Converter()
        with pytest.raises(ExtractionError):
            converter.convert(tmp_path / "missing.pdf")

    def test_output_error_on_bad_path(self, sample_pdf: Path, tmp_path: Path) -> None:
        # Create a file where we want a directory, so writing fails
        blocker = tmp_path / "blocker"
        blocker.write_text("i am a file")
        bad_out = blocker / "out.md"   # can't write: blocker is a file, not a dir
        converter = Converter()
        with pytest.raises(OutputError):
            converter.convert_to_file(sample_pdf, bad_out)
