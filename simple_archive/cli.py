"""CLI for working with Simple Archive Format."""

import logging
from pathlib import Path
from typing import Optional

import typer

from simple_archive.use_cases import CreateSimpleArchiveFromCSVWriteToPath

app = typer.Typer()


@app.command()
def main(
    input_file: Path,
    output: Optional[Path] = None,
    create_zip: bool = typer.Option(False, "--zip"),
) -> None:
    """Create Simple Archive from an csv."""
    logging.basicConfig(level=logging.DEBUG)
    uc = CreateSimpleArchiveFromCSVWriteToPath()
    uc.execute(input_path=input_file, output_path=output, create_zip=create_zip)
