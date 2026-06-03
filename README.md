# pdfcleanerx

Convert messy PDF-extracted text into clean Markdown files.

- **Fully offline** – no AI APIs, no cloud services
- **Modular pipeline** – swap or extend any layer
- **CLI + Python SDK**
- **Production-ready** – structured logging, custom exceptions, typed

---

## Installation

```bash
pip install pdfcleaner
```

### From source

```bash
git https://github.com/namanbhola1888/pdfcleaner
cd pdfcleanerx
pip install -e ".[dev]"
```

---

## Quick Start

### CLI

```bash
# Single file → writes output/report.md
pdfcleaner convert report.pdf

# Named output
pdfcleaner convert report.pdf --output clean.md

# Print to stdout
pdfcleaner convert report.pdf --stdout

# Batch (glob)
pdfcleaner convert docs/*.pdf --output-dir ./markdown

# Verbose / debug
pdfcleaner convert report.pdf --verbose
```

### Python SDK

```python
from pdfcleanerx import Converter

# Default: full pipeline → Markdown string
converter = Converter()
markdown = converter.convert("report.pdf")
print(markdown)

# Write directly to file
written_path = converter.convert_to_file("report.pdf", "report.md")
```

### Dependency injection (custom pipeline)

```python
from pdfcleanerx import Converter
from pdfcleanerx.cleaners import CleanerPipeline, WhitespaceCleaner, PageNumberCleaner

# Only run two cleaners
pipeline = CleanerPipeline([PageNumberCleaner(), WhitespaceCleaner()])
converter = Converter(pipeline=pipeline)
markdown = converter.convert("report.pdf")
```

---

## Configuration

Copy `.env.example` to `.env` and edit:

```bash
cp .env.example .env
```

Key settings:

| Variable | Default | Description |
|---|---|---|
| `LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `OUTPUT_DIR` | `./output` | Default output directory |
| `HEADING_FONT_SIZE_THRESHOLD` | `1.2` | Font size multiplier for heading detection |
| `CLEANER_PAGE_NUMBERS` | `true` | Enable/disable page-number removal |
| `CLEANER_LINE_WRAP` | `true` | Enable/disable line-wrap merging |
| `CLEANER_WHITESPACE` | `true` | Enable/disable whitespace normalisation |
| `CLEANER_HEADINGS` | `true` | Enable/disable heading detection |
| `FOOTER_REPEAT_THRESHOLD` | `3` | Pages a footer must repeat on to be stripped |

---

## Architecture

```
CLI (Typer)
    │
    ▼
Converter                  ← SDK entry point (dependency injection)
    │
    ├── BaseExtractor       ← pdfplumber (swappable)
    │       └── Document (pages → blocks + font metadata)
    │
    ├── CleanerPipeline     ← ordered chain
    │       ├── PageNumberCleaner
    │       ├── WhitespaceCleaner
    │       ├── HeadingDetector
    │       └── LineWrapCleaner
    │
    └── BaseFormatter       ← MarkdownFormatter (swappable)
```

### Adding a custom cleaner

```python
from pdfcleanerx.cleaners.base import BaseCleaner
from pdfcleanerx.models import Document

class MyCustomCleaner(BaseCleaner):
    def clean(self, document: Document) -> Document:
        for page in document.pages:
            for block in page.blocks:
                block.text = block.text.replace("©", "")
        return document

# Inject into Converter
from pdfcleanerx.cleaners import CleanerPipeline, PageNumberCleaner, WhitespaceCleaner
from pdfcleanerx import Converter

pipeline = CleanerPipeline([PageNumberCleaner(), WhitespaceCleaner(), MyCustomCleaner()])
converter = Converter(pipeline=pipeline)
```

### Adding a custom formatter (e.g. HTML)

```python
from pdfcleanerx.formatter.base import BaseFormatter
from pdfcleanerx.models import Document

class HtmlFormatter(BaseFormatter):
    def format(self, document: Document) -> str:
        parts = ["<html><body>"]
        for page in document.pages:
            for block in page.blocks:
                level = getattr(block, "_heading_level", 0)
                if level:
                    parts.append(f"<h{level}>{block.text}</h{level}>")
                else:
                    parts.append(f"<p>{block.text}</p>")
        parts.append("</body></html>")
        return "\n".join(parts)

converter = Converter(formatter=HtmlFormatter())
```

---

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=pdfcleanerx --cov-report=html

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

---

## Build & Publish to PyPI

### Prerequisites

```bash
pip install build twine
```

### Build

```bash
python -m build
# Creates dist/pdfcleanerx-0.1.0.tar.gz and dist/pdfcleanerx-0.1.0-py3-none-any.whl
```

### Test on TestPyPI first (recommended)

```bash
twine upload --repository testpypi dist/*
pip install --index-url https://test.pypi.org/simple/ pdfcleanerx
```

### Publish to PyPI

```bash
twine upload dist/*
```

You will be prompted for your PyPI API token.  Store it in `~/.pypirc` or set:

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-<your-token>
```

### Bump version

Edit `version` in `pyproject.toml` and `src/pdfcleanerx/__init__.py`, then rebuild.

---

## License

MIT
