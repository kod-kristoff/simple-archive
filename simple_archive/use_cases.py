"""Use cases for simple archive."""

from pathlib import Path
from typing import Optional, Union

from simple_archive import SimpleArchive


class CreateSimpleArchiveFromCSVWriteToPath:
    """Create a Simple Archive from a CSV file and write to Path."""

    def execute(  # noqa: PLR6301
        self,
        input_path: Path,
        output_path: Optional[Path] = None,
        create_zip: bool = False,
    ) -> None:
        """Create a Simple Archive from a CSV file and write to Path.

        Args:
            input_path (Path): path to csv file
            output_path (Optional[Path], optional): A directory or an filename with extension '.zip'. Defaults to None.
            create_zip (bool, optional): if True writes a zip file. Defaults to False.
        """  # noqa: E501
        if not output_path:
            output_path = create_unique_path(
                Path("output"), input_path.stem, "zip" if create_zip else None
            )
        elif output_path.suffix == "zip":
            create_zip = True
        if create_zip:
            output_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            output_path.mkdir(parents=True, exist_ok=False)

        simple_archive = SimpleArchive.from_csv_path(input_path)

        if create_zip:
            simple_archive.write_to_zip(output_path)
        else:
            simple_archive.write_to_path(output_path)


def create_unique_path(base_path: Path, base_stem: str, suffix: Optional[str] = None) -> Path:
    """Create a unique path in base_path using base_stem and optional suffix.

    Args:
        base_path (Path): the path to work with
        base_stem (str): the stem to use for the path
        suffix (Optional[str], optional): suffix to use. Defaults to None.

    Returns:
        Path: an unique path in base_path
    """
    new_path = mk_path(base_path, base_stem, suffix)
    counter = 1
    while new_path.exists():
        new_path = mk_path(base_path, f"{base_stem}.{counter:03d}", suffix)
        counter += 1
    return new_path


def mk_path(base: Path, stem: Union[Path, str], suffix: Optional[str] = None) -> Path:
    """Create a path from base and stem and suffix is given.

    >>> str(mk_path(Path('tmp'), 'simple'))
    'tmp/simple'
    >>> str(mk_path(Path('tmp'), 'simple', 'zip'))
    'tmp/simple.zip'

    Args:
        base (Path): the base to use
        stem (Path | str): the stem to add
        suffix (Optional[str]): the optional suffix to add

    Returns:
        Path: the create path
    """
    return base / f"{stem}.{suffix}" if suffix else base / stem
