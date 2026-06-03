"""Command-line interface for pdfcleanerx.

Usage examples::

    # Single file → stdout
    pdfcleanerx convert report.pdf

    # Single file → named output
    pdfcleanerx convert report.pdf --output report.md

    # Batch: all PDFs in a directory → ./output/
    pdfcleanerx convert docs/*.pdf --output-dir ./output

    # Verbose
    pdfcleanerx convert report.pdf -v
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from pdfcleanerx.__init__ import __version__
from pdfcleanerx.config import get_config
from pdfcleanerx.converter import Converter
from pdfcleanerx.exceptions import PdfCleanerXError
from pdfcleanerx.logging_setup import setup_logging

app = typer.Typer(
    name="pdfcleanerx",
    help="Convert messy PDF-extracted text into clean Markdown files.",
    no_args_is_help=True,
    add_completion=False,
)

_console = Console(stderr=True)
_out_console = Console()  # stdout for piped output


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"pdfcleanerx {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(  # noqa: B008
        False,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """pdfcleanerx – PDF to Markdown converter."""


@app.command()
def convert(
    pdf_files: list[Path] = typer.Argument(  # noqa: B008
        ...,
        help="One or more PDF files to convert.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    output: Path | None = typer.Option(  # noqa: B008
        None,
        "--output",
        "-o",
        help="Output .md file path (single-file mode only).",
    ),
    output_dir: Path | None = typer.Option(  # noqa: B008
        None,
        "--output-dir",
        "-d",
        help="Directory for output .md files (batch mode).  Defaults to config OUTPUT_DIR.",
    ),
    stdout: bool = typer.Option(  # noqa: B008
        False,
        "--stdout",
        "-s",
        help="Print Markdown to stdout instead of writing a file.",
    ),
    verbose: bool = typer.Option(  # noqa: B008
        False,
        "--verbose",
        "-v",
        help="Enable debug logging.",
    ),
) -> None:
    """Convert one or more PDF files to clean Markdown."""
    cfg = get_config()
    log_level = logging.DEBUG if verbose else cfg.log_level
    setup_logging(log_level)

    # Validate: --output only makes sense for a single file
    if output and len(pdf_files) > 1:
        _console.print(
            "[red]Error:[/red] --output can only be used with a single PDF file."
        )
        raise typer.Exit(code=1)

    converter = Converter(config=cfg)
    failed = 0

    for pdf_path in pdf_files:
        try:
            if stdout:
                markdown = converter.convert(pdf_path)
                _out_console.print(markdown, markup=False, highlight=False)
            else:
                out_path = output
                if out_path is None:
                    base = output_dir or cfg.output_dir
                    out_path = base / (pdf_path.stem + ".md")

                written = converter.convert_to_file(pdf_path, out_path)
                _console.print(f"[green]✓[/green] {pdf_path.name} → {written}")

        except PdfCleanerXError as exc:
            _console.print(
                Panel(
                    str(exc),
                    title=f"[red]Error processing {pdf_path.name}[/red]",
                    border_style="red",
                )
            )
            failed += 1
        except Exception as exc:  # noqa: BLE001
            _console.print(
                Panel(
                    f"Unexpected error: {exc}\nRun with --verbose for details.",
                    title=f"[red]Error processing {pdf_path.name}[/red]",
                    border_style="red",
                )
            )
            logging.getLogger("pdfcleanerx").debug("Traceback:", exc_info=True)
            failed += 1

    if failed:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
