"""Model for Simple Archive."""

import csv
import logging
import re
import zipfile
from datetime import date
from pathlib import Path
from typing import IO, Any, Optional, Union
from xml.etree.ElementTree import Element, ElementTree, SubElement

import pydantic
from typing_extensions import Self

from simple_archive.file_system import (
    FileSystem,
    PathFileSystem,
    ZipFileSystem,
)

DEFAULT_ENCODING = "utf-8"


logger = logging.getLogger(__name__)


class DublinCoreDate(pydantic.BaseModel):
    """Dublin Core Date model."""

    issued: date


class DublinCoreElement(pydantic.BaseModel):
    """Dublin Core Element model."""

    element: str
    value: str
    qualifier: Optional[str] = None
    language: Optional[str] = None


LANGUAGE_IN_SQUARE_BRACKETS = re.compile(r"\[([a-zA-Z_]+)\]")


class DublinCore(pydantic.RootModel):
    """Dublin Core model."""

    root: list[DublinCoreElement]

    @pydantic.model_validator(mode="before")
    @classmethod
    def build_list_from_dict_if_needed(cls, values: Any) -> list:  # noqa: D102
        if isinstance(values, list):
            return values
        new_values = []
        for key, value in values.items():
            if isinstance(value, str):
                new_value = {"element": key, "value": value}
                if lang := LANGUAGE_IN_SQUARE_BRACKETS.search(key):
                    new_value["element"] = key[: lang.start()]
                    new_value["language"] = lang.group(1)
                new_values.append(new_value)
            elif isinstance(value, dict):
                new_value = {"element": key}
                for key1, value1 in value.items():
                    if key1 == "value":
                        new_value["value"] = value1
                    elif key1 == "language":
                        new_value["language"] = value1
                    else:
                        new_value["qualifier"] = key1
                        new_value["value"] = value1
                new_values.append(new_value)
        return new_values


def build_xml(dc: DublinCore, *, schema: str) -> ElementTree:
    """Build an ElementTree from a DublinCore model.

    Args:
        dc (DublinCore): the model to build from
        schema (str): the schema to annotate dublin_core with

    Returns:
        ElementTree: the resulting ElementTree
    """
    root = Element("dublin_core", attrib={"schema": schema})
    for element in dc.root:
        dcvalue(
            root,
            element=element.element,
            qualifier=element.qualifier,
            language=element.language,
            text=element.value,
        )
    return ElementTree(root)


def dcvalue(
    parent: Element,
    element: str,
    qualifier: Optional[str] = None,
    language: Optional[str] = None,
    text: Optional[str] = None,
) -> Element:
    """Create a dcvalue subelement of parent.

    Args:
        parent (Element): the element to use as parent
        element (str): the element tag
        qualifier (Optional[str], optional): qualifier to use. Defaults to None.
        language (Optional[str], optional): language if any. Defaults to None.
        text (Optional[str], optional): Text to set on elem. Defaults to None.

    Returns:
        Element: _description_
    """
    attribs = {
        "element": element,
        "qualifier": qualifier or "none",
    }
    if language:
        attribs["language"] = language
    elem = SubElement(parent, "dcvalue", attrib=attribs)
    if text:
        elem.text = text
    return elem


class Metadata(pydantic.BaseModel):
    """Model of metadata."""

    model_config = pydantic.ConfigDict(extra="forbid")

    dc: DublinCore
    local: Optional[DublinCore] = None
    dcterms: Optional[DublinCore] = None
    metashare: Optional[DublinCore] = None

    @pydantic.field_validator("dcterms")
    @classmethod
    def set_language_for_dcterms(cls, v: Optional[DublinCore]) -> Optional[DublinCore]:
        """Set language if not set."""
        if not v:
            return v
        for elem in v.root:
            if elem.language is None:
                elem.language = "*"
        return v

    @pydantic.field_validator("metashare")
    @classmethod
    def set_language_for_metashare(cls, v: Optional[DublinCore]) -> Optional[DublinCore]:
        """Set language if not set."""
        if not v:
            return v
        for elem in v.root:
            if elem.language is None:
                elem.language = "en_US"
        return v


class Item(pydantic.BaseModel):
    """Simple Archive Item model."""

    files: list[Path]
    metadata: Metadata

    @pydantic.field_validator("files", mode="before")
    @classmethod
    def split_str(cls, v: Any) -> Any:  # noqa: D102
        if isinstance(v, str):
            return v.split("||") if v else []
        return v

    @pydantic.model_validator(mode="after")
    def check_if_has_files(self) -> Self:  # noqa: D102
        if len(self.files) > 0:
            elem = DublinCoreElement(element="has", value="yes", qualifier="files")
        else:
            elem = DublinCoreElement(element="has", value="no", qualifier="files")

        if self.metadata.local is None:
            self.metadata.local = DublinCore(root=[elem])
            return self
        for local_elem in self.metadata.local.root:
            if local_elem.element == elem.element and local_elem.qualifier == elem.qualifier:
                local_elem.value = elem.value
                return self

        self.metadata.local.root.append(elem)
        return self

    @pydantic.model_validator(mode="before")
    @classmethod
    def unflatten_values(cls, values: Any) -> dict:  # noqa: D102
        nested: dict = {}
        for key, value in values.items():
            parts = key.split(".")
            sub = nested

            for part in parts[:-1]:
                if part not in sub:
                    sub[part] = {}
                sub = sub[part]

            sub[parts[-1]] = value
        new_values: dict = {"metadata": {}}
        for key, value in nested.items():
            if key == "files":
                new_values["files"] = value
            elif isinstance(value, pydantic.BaseModel):
                new_values[key] = value
            else:
                new_values["metadata"][key] = value
        return new_values


class SimpleArchive:
    """Simple Archive model."""

    def __init__(self, input_folder: Path, items: list[Item]) -> None:  # noqa: D107
        self.input_folder = input_folder
        self.items = items

    @classmethod
    def from_csv_path(cls, csv_path: Path) -> "SimpleArchive":  # noqa: D102
        items = []
        with open(csv_path, encoding=DEFAULT_ENCODING, newline="") as csvfile:  # noqa: PTH123
            reader = csv.DictReader(csvfile)
            for row in reader:
                item = Item(**row)
                items.append(item)
        return cls(input_folder=csv_path.parent, items=items)

    def write_to_path(self, output_path: Path) -> None:  # noqa: D102
        path_fs = PathFileSystem(output_path)
        self._write_to_fs(path_fs)

    def write_to_zip(self, output_path: Path) -> None:  # noqa: D102
        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
            zip_fs = ZipFileSystem(zipf)
            self._write_to_fs(zip_fs)

    def _write_to_fs(self, fs: FileSystem) -> None:
        for item_nr, item in enumerate(self.items):
            item_path = f"item_{item_nr:03d}"
            fs.mkdir(item_path)

            self._write_contents_file(item, item_path, fs)
            self._copy_files(item, item_path, fs)
            self._write_metadata(item.metadata, item_path, fs)

    def _write_contents_file(self, item: Item, item_path: str, fs: FileSystem) -> None:  # noqa: PLR6301
        contents_path = f"{item_path}/contents"
        logger.info("writing '%s'", contents_path)
        with fs.open_text(contents_path) as contents_file:
            for file_path in item.files:
                contents_file.write(file_path.name)
                contents_file.write("\n")

    def _copy_files(self, item: Item, item_path: str, fs: FileSystem) -> None:
        for file_path in item.files:
            src_path = self.input_folder / file_path
            dst_path = f"{item_path}/{file_path}"
            logger.info("  copying '%s to '%s'", src_path, dst_path)
            fs.copy(src_path, dst_path)

    def _write_metadata(self, metadata: Metadata, item_path: str, fs: FileSystem) -> None:  # noqa: PLR6301
        with fs.open_bytes(f"{item_path}/dublin_core.xml") as dc_file:
            build_and_write_metadata(metadata.dc, schema="dc", path_or_file=dc_file)

        if metadata.local:
            with fs.open_bytes(f"{item_path}/metadata_local.xml") as local_file:
                build_and_write_metadata(metadata.local, schema="local", path_or_file=local_file)
        if metadata.dcterms:
            with fs.open_bytes(f"{item_path}/metadata_dcterms.xml") as dcterms_file:
                build_and_write_metadata(
                    metadata.dcterms, schema="dcterms", path_or_file=dcterms_file
                )
        if metadata.metashare:
            with fs.open_bytes(f"{item_path}/metadata_metashare.xml") as metashare_file:
                build_and_write_metadata(
                    metadata.metashare, schema="metashare", path_or_file=metashare_file
                )


def build_and_write_metadata(
    metadata: DublinCore, schema: str, path_or_file: Union[Path, IO[bytes]]
) -> None:
    """Build and write metadata.

    Args:
        metadata (DublinCore): metadata to build
        schema (str): schema to use
        path_or_file (Union[Path, IO[bytes]]): path or file to write to
    """
    metadata_xml = build_xml(metadata, schema=schema)
    metadata_xml.write(path_or_file, encoding="utf-8", xml_declaration=True)
