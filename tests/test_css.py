from src.css import CSSParser, TagSelector, DescendantSelector
from src.dom import Element


def test_tag_selector_matches():
    tag_selector = TagSelector("p")
    assert tag_selector.matches(Element(tag="p", attributes={}))


def test_tag_selector_does_not_match():
    tag_selector = TagSelector("p")
    assert not tag_selector.matches({"tag": "div"})


def test_descendant_selector_matches():
    descendant_selector = DescendantSelector(
        TagSelector("div"), TagSelector("p")
    )
    assert descendant_selector.matches(
        Element(tag="p", attributes={}, parent=Element(tag="div", attributes={}))
    )


def test_descendant_selector_does_not_match():
    descendant_selector = DescendantSelector(
        TagSelector("div"), TagSelector("p")
    )
    assert not descendant_selector.matches(
        {"tag": "p", "parent": {"tag": "span"}}
    )


def test_css_parser():
    css = """
    div p {
        color: red;
    }
    """
    parser = CSSParser(css)
    rules = parser.parse()
    assert len(rules) == 1
    selector, body = rules[0]
    assert isinstance(selector, DescendantSelector)
    assert selector.ancestor.tag == "div"
    assert selector.descendant.tag == "p"
    assert body == {"color": "red"}
