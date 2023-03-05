from pathlib import Path

import typer

from simple_archive.use_cases import CreateSimpleArchiveFromCSV

app = typer.Typer()


@app.command()
def main(file: Path):
    """Create Simple Archive from an csv."""

    uc = CreateSimpleArchiveFromCSV()
    simple_archive = uc.execute(file)
