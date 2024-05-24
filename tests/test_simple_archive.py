import shutil
import xml.etree.ElementTree as ET  # noqa: N817
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Optional

import pytest

from simple_archive.simple_archive import (
    DublinCore,
    DublinCoreElement,
    Item,
    Metadata,
    SimpleArchive,
    build_and_write_metadata,
)


def test_item() -> None:
    values = {"files": "simple.txt", "dc.title": "Simple"}
    item = Item(**values)

    expected = Item(
        files=["simple.txt"],
        metadata=Metadata(
            dc=DublinCore(root=[DublinCoreElement(element="title", value="Simple")])
        ),
    )
    assert item == expected


def test_dublin_core_with_language() -> None:
    data = {
        "files": "",
        "dc.description[sv_SE]": "beskrivning",
    }
    item = Item(**data)

    actual = BytesIO()
    build_and_write_metadata(item.metadata.dc, schema="dc", path_or_file=actual)

    assert (
        actual.getvalue()
        == b'<?xml version=\'1.0\' encoding=\'utf-8\'?>\n<dublin_core schema="dc"><dcvalue element="description" qualifier="none" language="sv_SE">beskrivning</dcvalue></dublin_core>'  # noqa: E501
    )


@pytest.fixture(name="simple_archive")
def fixture_simple_archive() -> SimpleArchive:
    data = {
        "files": "values.txt",
        "dc.title": "Empty",
        "local.branding": "Språkbanken Text",
        "local.size.info": "2@@tokens",
        "dcterms.alternative": "x-empty",
        "metashare.ResourceInfo#ContentInfo.mediaType": "text",
    }
    return SimpleArchive(input_folder=Path("tests/data"), items=[Item(**data)])


def test_simple_archive_write_to_path(simple_archive: SimpleArchive) -> None:
    output = Path("tests/data/gen/simple_archive_write_to_path")
    shutil.rmtree(output, ignore_errors=True)
    simple_archive.write_to_path(output)

    contents_path = output / "item_000/contents"
    assert contents_path.exists()
    root = ET.parse(output / "item_000/dublin_core.xml").getroot()
    _assert_schema_element_value(root, "dc", "./dcvalue[@element='title']", "Empty")

    root = ET.parse(output / "item_000/metadata_local.xml").getroot()
    _assert_schema_element_value(
        root,
        "local",
        "./dcvalue[@element='branding']",
        "Språkbanken Text",
    )
    assert root.find("./dcvalue[@element='size'][@qualifier='info']").text == "2@@tokens"  # type: ignore[union-attr]
    assert root.find("./dcvalue[@element='has'][@qualifier='files']").text == "yes"  # type: ignore[union-attr]

    root = ET.parse(output / "item_000/metadata_dcterms.xml").getroot()
    _assert_schema_element_value(
        root,
        "dcterms",
        "./dcvalue[@element='alternative']",
        "x-empty",
        expected_attribs={"language": "*"},
    )

    root = ET.parse(output / "item_000/metadata_metashare.xml").getroot()
    _assert_schema_element_value(
        root,
        "metashare",
        "./dcvalue[@element='ResourceInfo#ContentInfo'][@qualifier='mediaType']",
        "text",
        expected_attribs={"language": "en_US"},
    )


def test_simple_archive_write_to_zip(simple_archive: SimpleArchive) -> None:
    output = Path("tests/data/gen/simple_archive_write_to_zip.zip")
    output.unlink(missing_ok=True)
    simple_archive.write_to_zip(output)

    with zipfile.ZipFile(output) as zipf:
        with zipf.open("item_000/dublin_core.xml") as dc_file:
            root = ET.parse(dc_file).getroot()
            _assert_schema_element_value(root, "dc", "./dcvalue[@element='title']", "Empty")
        with zipf.open("item_000/metadata_local.xml") as local_file:
            root = ET.parse(local_file).getroot()
            _assert_schema_element_value(
                root, "local", "./dcvalue[@element='branding']", "Språkbanken Text"
            )
            assert root.find("./dcvalue[@element='size'][@qualifier='info']").text == "2@@tokens"  # type: ignore[union-attr]
            assert root.find("./dcvalue[@element='has'][@qualifier='files']").text == "yes"  # type: ignore[union-attr]
        with zipf.open("item_000/metadata_dcterms.xml") as dcterms_file:
            root = ET.parse(dcterms_file).getroot()
            _assert_schema_element_value(
                root,
                "dcterms",
                "./dcvalue[@element='alternative']",
                "x-empty",
                expected_attribs={"language": "*"},
            )
        with zipf.open("item_000/metadata_metashare.xml") as metashare_file:
            root = ET.parse(metashare_file).getroot()
            _assert_schema_element_value(
                root,
                "metashare",
                "./dcvalue[@element='ResourceInfo#ContentInfo'][@qualifier='mediaType']",
                "text",
                expected_attribs={"language": "en_US"},
            )


def _assert_schema_element_value(
    root: ET.Element,
    expected_schema: str,
    path: str,
    expected_text: str,
    expected_attribs: Optional[dict[str, str]] = None,
) -> None:
    assert root.find(".").attrib["schema"] == expected_schema  # type: ignore[union-attr]
    elem = root.find(path)
    assert elem is not None
    assert elem.text == expected_text
    if expected_attribs:
        for key, value in expected_attribs.items():
            assert key in elem.attrib
            assert elem.attrib[key] == value
