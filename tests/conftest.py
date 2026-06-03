"""Shared pytest fixtures."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from pdfcleanerx.models import Document, PageData, TextBlock

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_generate_fixture():
    spec = importlib.util.spec_from_file_location(
        "generate_fixture", FIXTURES_DIR / "generate_fixture.py"
    )
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


@pytest.fixture(scope="session")
def sample_pdf(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Generate a sample PDF and return its path."""
    mod = _load_generate_fixture()
    out = tmp_path_factory.mktemp("pdfs") / "sample.pdf"
    mod.build_sample_pdf(out)
    return out


def make_block(
    text: str,
    font_size: float | None = 12.0,
    page_num: int = 1,
    is_bold: bool = False,
) -> TextBlock:
    return TextBlock(
        text=text,
        font_size=font_size,
        page_num=page_num,
        is_bold=is_bold,
    )


def make_document(*pages_text: list) -> Document:
    pages = []
    for i, lines in enumerate(pages_text, start=1):
        blocks = [make_block(line, page_num=i) for line in lines]
        pages.append(PageData(page_num=i, blocks=blocks))
    return Document(pages=pages)


@pytest.fixture()
def simple_document() -> Document:
    return make_document(
        ["Introduction", "This is body text.", "42"],
        ["1. Background", "More body text here."],
    )
