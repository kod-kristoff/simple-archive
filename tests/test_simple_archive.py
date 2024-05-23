import shutil
import xml.etree.ElementTree as ET  # noqa: N817
from io import BytesIO
from pathlib import Path

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
        == b'<dublin_core schema="dc"><dcvalue element="description" qualifier="none" language="sv_SE">beskrivning</dcvalue></dublin_core>'  # noqa: E501
    )


def test_simple_archive() -> None:
    data = {"files": "", "dc.title": "Empty"}
    simar = SimpleArchive(input_folder=Path("tests/data"), items=[Item(**data)])

    output = Path("tests/data/gen/simple_archive")
    shutil.rmtree(output)
    simar.write_to_path(output)

    tree = ET.parse(output / "item_000/dublin_core.xml")
    root = tree.getroot()
    assert root.find(".").attrib["schema"] == "dc"
    assert root.find("./dcvalue[@element='title']").text == "Empty"
