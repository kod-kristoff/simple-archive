from io import BytesIO

from simple_archive.simple_archive import (
    DublinCore,
    DublinCoreElement,
    Item,
    Metadata,
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
