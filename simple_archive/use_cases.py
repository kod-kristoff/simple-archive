from pathlib import Path
from typing import Optional, Union

from simple_archive import SimpleArchive


class CreateSimpleArchiveFromCSVWriteToPath:
    def execute(
        self,
        input_path: Path,
        output_path: Optional[Path] = None,
        create_zip: bool = False,
    ) -> None:
        if not output_path:
            output_path = create_unique_path(
                Path("output"), input_path.stem, "zip" if create_zip else None
            )
        else:
            if output_path.suffix == "zip":
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


def create_unique_path(
    base_path: Path, base_stem: str, suffix: Optional[str] = None
) -> Path:
    new_path = mk_path(base_path, base_stem, suffix)
    counter = 1
    while new_path.exists():
        new_path = mk_path(base_path, f"{base_stem}.{counter:03d}", suffix)
        counter += 1
    return new_path


def mk_path(base: Path, stem: Union[Path, str], suffix: Optional[str]) -> Path:
    return base / f"{stem}.{suffix}" if suffix else base / stem
