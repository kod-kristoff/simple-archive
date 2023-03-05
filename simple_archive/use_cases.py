from pathlib import Path

from simple_archive import SimpleArchive


class CreateSimpleArchiveFromCSV:
    def execute(self, file: Path) -> SimpleArchive:
        return SimpleArchive()
