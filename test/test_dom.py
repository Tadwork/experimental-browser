from src.dom import HTMLParser, Element, Text

def test_html_parser_single_tag():
    parser = HTMLParser("<p>hello world</p>")
    result = parser.parse()
    assert len(result.children) == 1
    assert isinstance(result.children[0], Element)
    assert result.children[0].tag == "p"
    assert len(result.children[0].children) == 1
    assert isinstance(result.children[0].children[0], Text)
    assert result.children[0].children[0].text == "hello world"

def test_html_parser_nested_tags():
    parser = HTMLParser("<p><b>hello</b> world</p>")
    result = parser.parse()
    assert len(result.children) == 1
    assert isinstance(result.children[0], Element)
    assert result.children[0].tag == "p"
    assert len(result.children[0].children) == 2
    assert isinstance(result.children[0].children[0], Element)
    assert result.children[0].children[0].tag == "b"
    assert isinstance(result.children[0].children[1], Text)
    assert result.children[0].children[1].text == " world"

def test_html_parser_empty_tag():
    parser = HTMLParser("<p></p>")
    result = parser.parse()
    assert len(result.children) == 1
    assert isinstance(result.children[0], Element)
    assert result.children[0].tag == "p"
    assert len(result.children[0].children) == 0

def test_html_parser_multiple_tags():
    parser = HTMLParser("<p>hello</p><p>world</p>")
    result = parser.parse()
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

def test_html_parser_special_characters():
    parser = HTMLParser("<p>&lt;hello&gt;</p>")
    result = parser.parse()
    assert len(result.children) == 1
    assert isinstance(result.children[0], Element)
    assert result.children[0].tag == "p"
    assert len(result.children[0].children) == 1
    assert isinstance(result.children[0].children[0], Text)
    assert result.children[0].children[0].text == "<hello>"