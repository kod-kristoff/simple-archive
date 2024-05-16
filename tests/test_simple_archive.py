from simple_archive.simple_archive import DublinCore, DublinCoreElement, Item


def test_item() -> None:
    values = {"files": "simple.txt", "dc.title": "Simple"}
    item = Item(**values)

    expected = Item(
        files=["simple.txt"],
        dc=DublinCore(elements=[DublinCoreElement(element="title", value="Simple")]),
    )
    assert item == expected
