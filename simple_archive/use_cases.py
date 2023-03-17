from pathlib import Path
from typing import Optional

from simple_archive import SimpleArchive


class CreateSimpleArchiveFromCSVWriteToPath:
    def execute(self, input_path: Path, output_path: Optional[Path] = None) -> None:
        if not output_path:
            output_path = create_unique_path(Path("output"), input_path.stem)
        output_path.mkdir(parents=True, exist_ok=False)

        simple_archive = SimpleArchive.from_csv_path(input_path)

        simple_archive.write_to_path(output_path)


def create_unique_path(base_path: Path, base_stem: str) -> Path:
    new_path = base_path / base_stem
    counter = 1
    while new_path.exists():
        new_path = base_path / f"{base_stem}.{counter:03d}"
        counter += 1
    return new_path
