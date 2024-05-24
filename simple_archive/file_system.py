"""File system abstraction."""

import abc
import logging
import shutil
import zipfile
from io import TextIOWrapper
from pathlib import Path
from typing import IO

logger = logging.getLogger(__name__)


class FileSystem(abc.ABC):
    """Interface for working with a file system."""

    @abc.abstractmethod
    def mkdir(self, path: str) -> None:
        """Create the directory 'path'."""

    @abc.abstractmethod
    def open_text(self, path: str) -> IO[str]:
        """Open a file for writing text."""

    @abc.abstractmethod
    def open_bytes(self, path: str) -> IO[bytes]:
        """Open a file for writing bytes."""

    @abc.abstractmethod
    def copy(self, src_path: Path, dst_path: str) -> None:
        """Copy src_path to dst_path."""


class PathFileSystem(FileSystem):
    """File system for working with files relative to the given path."""

    def __init__(self, output_path: Path) -> None:
        """Create a file system relative to the given path.

        Args:
            output_path (Path): the path to work with
        """
        self.output_path = output_path

    @classmethod
    def _ensure_path(cls, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)

    def mkdir(self, path: str) -> None:
        """Create a dir relative to this file systems output_path.

        Args:
            path (str): the relative path
        """
        logger.info("creating '%s' ...", path)
        _path = self.output_path / path
        _path.mkdir(parents=True, exist_ok=False)

    def open_text(self, path: str) -> IO[str]:
        """Open a file for writing text relative to output_path.

        Creates 'self.output_path' if it don't exists.

        Args:
            path (str): the relative path to open

        Returns:
            IO[str]: the open file
        """
        _path = self.output_path / path
        self._ensure_path(_path.parent)
        return _path.open(mode="w", encoding="utf-8")

    def open_bytes(self, path: str) -> IO[bytes]:
        """Open a file for writing bytes relative to output_path.

        Creates 'self.output_path' if it don't exists.

        Args:
            path (str): the relative path to open

        Returns:
            IO[bytes]: the open file
        """
        _path = self.output_path / path
        self._ensure_path(_path.parent)
        return _path.open(mode="wb")

    def copy(self, src_path: Path, dst_path: str) -> None:
        """Copy dst_path to src_path relative to this path.

        Args:
            src_path (Path): the path to copy
            dst_path (str): the relative path to copy to
        """
        dst = self.output_path / dst_path
        self._ensure_path(dst.parent)
        shutil.copy(src_path, dst)


class ZipFileSystem(FileSystem):
    """Treat a zip archive as a file system."""

    def __init__(self, zipf: zipfile.ZipFile) -> None:
        """Create."""
        self.zipf = zipf

    def mkdir(self, path: str) -> None:
        """Make a directory.

        No-op for this class.
        """

    def open_text(self, path: str) -> IO[str]:
        """Open a file for writing text at the relative path given.

        Args:
            path (str): the relative path

        Returns:
            IO[str]: the open file
        """
        return TextIOWrapper(self.zipf.open(path, "w"), encoding="utf-8")

    def open_bytes(self, path: str) -> IO[bytes]:
        """Open a file for writing bytes at the relative path given.

        Args:
            path (str): the relative path

        Returns:
            IO[bytes]: the open file
        """
        return self.zipf.open(path, "w")

    def copy(self, src_path: Path, dst_path: str) -> None:
        """Copy the src_path to relative path dst_path.

        Args:
            src_path (Path): the source path
            dst_path (str): the relative destination path
        """
        self.zipf.write(src_path, dst_path)
