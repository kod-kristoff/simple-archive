from xml.etree import ElementTree

from simple_archive.simple_archive import DublinCore, build_xml


def test_dublin_core() -> None:
    data = {"contributor.author": "contributor.author"}
    dc = DublinCore(**data)  # type:ignore[arg-type]

    tree = build_xml(dc, schema="dc")
    xml = ElementTree.tostring(tree.getroot())

    assert (
        xml
        == b'<dublin_core schema="dc"><dcvalue element="contributor.author" qualifier="none">contributor.author</dcvalue></dublin_core>'  # noqa: E501
    )


def test_dublin_core_with_language() -> None:
    data = {"description": {"language": "sv_SE", "value": "beskrivning"}}
    dc = DublinCore(**data)  # type:ignore[arg-type]

    tree = build_xml(dc, schema="dc")
    xml = ElementTree.tostring(tree.getroot())

    assert (
        xml
        == b'<dublin_core schema="dc"><dcvalue element="description" qualifier="none" language="sv_SE">beskrivning</dcvalue></dublin_core>'  # noqa: E501
    )


def test_dublin_core_with_language_in_square_brackets() -> None:
    data = {"description[sv_SE]": "beskrivning"}
    dc = DublinCore(**data)  # type:ignore[arg-type]

    tree = build_xml(dc, schema="dc")
    xml = ElementTree.tostring(tree.getroot())

    assert (
        xml
        == b'<dublin_core schema="dc"><dcvalue element="description" qualifier="none" language="sv_SE">beskrivning</dcvalue></dublin_core>'  # noqa: E501
    )
