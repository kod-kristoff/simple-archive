"""Model for Simple Archive."""

import csv
import logging
import re
import shutil
from datetime import date
from pathlib import Path
from typing import IO, Any, Optional, Union
from xml.etree.ElementTree import Element, ElementTree, SubElement
from zipfile import ZIP_DEFLATED, ZipFile

import pydantic

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
                value["element"] = key
                new_values.append(value)
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

    dc: DublinCore


class Item(pydantic.BaseModel):
    """Simple Archive Item model."""

    files: list[Path]
    metadata: Metadata

    @pydantic.field_validator("files", mode="before")
    @classmethod
    def split_str(cls, v: Any) -> Any:  # noqa: D102
        return v.split("||") if isinstance(v, str) else v

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
        for item_nr, item in enumerate(self.items):
            item_path = output_path / f"item_{item_nr:03d}"
            logger.info("creating '%s' ...", item_path)
            item_path.mkdir(parents=True, exist_ok=False)

            self.write_contents_file(item, item_path)
            self.copy_files(item, item_path)
            build_and_write_metadata(
                item.metadata.dc, schema="dc", path_or_file=item_path / "dublin_core.xml"
            )

    def write_to_zip(self, output_path: Path) -> None:  # noqa: D102
        with ZipFile(output_path, "w", compression=ZIP_DEFLATED) as zipfile:
            for item_nr, item in enumerate(self.items):
                item_path = f"item_{item_nr:03d}"
                # zipfile.mkdir(item_path)
                # copy files
                for file_path in item.files:
                    src_path = self.input_folder / file_path
                    dst_path = f"{item_path}/{file_path}"
                    zipfile.write(src_path, dst_path)
                # write contents
                contents_path = f"{item_path}/contents"
                with zipfile.open(contents_path, "w") as contents_file:
                    for file_path in item.files:
                        contents_file.write(file_path.name.encode("utf-8"))
                        contents_file.write(b"\n")
                # write metadata
                dublin_core_path = f"{item_path}/dublin_core.xml"
                logger.info("writing '%s'in zip-archive ", dublin_core_path)
                with zipfile.open(dublin_core_path, "w") as dublin_core_file:
                    build_and_write_metadata(
                        item.metadata.dc, schema="dc", path_or_file=dublin_core_file
                    )

    def write_contents_file(self, item: Item, item_path: Path) -> None:  # noqa: PLR6301, D102
        contents_path = item_path / "contents"
        logger.info("writing '%s'", contents_path)
        with contents_path.open(mode="w", encoding="utf-8") as contents_file:
            for file_path in item.files:
                contents_file.write(file_path.name)
                contents_file.write("\n")

    def copy_files(self, item: Item, item_path: Path) -> None:  # noqa: D102
        for file_path in item.files:
            src_path = self.input_folder / file_path
            dst_path = item_path
            logger.info("  copying '%s to '%s'", src_path, dst_path)
            shutil.copy(src_path, dst_path)


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
    metadata_xml.write(path_or_file)
