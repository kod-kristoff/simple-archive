import logging
from pathlib import Path
from typing import Optional

import typer

from simple_archive.use_cases import CreateSimpleArchiveFromCSVWriteToPath

app = typer.Typer()


@app.command()
def main(input_file: Path, output: Optional[Path] = None):
    """Create Simple Archive from an csv."""
    logging.basicConfig(level=logging.DEBUG)
    uc = CreateSimpleArchiveFromCSVWriteToPath()
    uc.execute(input_path=input_file, output_path=output)
