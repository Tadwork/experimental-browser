from src.dom import HTMLParser, Element, Text

### utility func
def add_implicit_tags(body):
    return f"<html><head></head><body>{body}</body></html>"
def get_body(node):
    return node.children[1]

### HTMLParser tests ###
def test_html_parser_single_tag():
    parser = HTMLParser(add_implicit_tags("<p>hello world</p>"))
    result = get_body(parser.parse()).children[0]
    assert isinstance(result, Element)
    assert result.tag == "p"
    assert len(result.children) == 1
    assert isinstance(result.children[0], Text)
    assert result.children[0].text == "hello world"

def test_html_parser_nested_tags():
    parser = HTMLParser(add_implicit_tags("<p><b>hello</b> world</p>"))
    result = get_body(parser.parse()).children[0]
    assert isinstance(result, Element)
    assert result.tag == "p"
    assert len(result.children) == 2
    assert isinstance(result.children[0], Element)
    assert result.children[0].tag == "b"
    assert isinstance(result.children[1], Text)
    assert result.children[1].text == " world"

def test_html_parser_empty_tag():
    parser = HTMLParser(add_implicit_tags("<p></p>"))
    result = get_body(parser.parse()).children[0]
    assert isinstance(result, Element)
    assert result.tag == "p"
    assert len(result.children) == 0

def test_html_parser_multiple_tags():
    parser = HTMLParser(add_implicit_tags("<p>hello</p><p>world</p>"))
    result = get_body(parser.parse())
    assert len(result.children) == 2
    assert isinstance(result.children[0], Element)
    assert result.children[0].tag == "p"
    assert len(result.children[0].children) == 1
    assert isinstance(result.children[0].children[0], Text)
    assert result.children[0].children[0].text == "hello"
    assert isinstance(result.children[1], Element)
    assert result.children[1].tag == "p"
    assert len(result.children[1].children) == 1
    assert isinstance(result.children[1].children[0], Text)
    assert result.children[1].children[0].text == "world"