import pytest

from src.window import lex, Text, Tag

def test_lex_no_tags():
    assert lex("hello world") == [Text("hello world")]

def test_lex_single_tag():
    assert lex("<p>hello world</p>") == [Tag("p"),Text("hello world"),Tag("/p")]

def test_lex_nested_tags():
    assert lex("<p><b>hello</b> world</p>") == [Tag("p"),Tag("b"),Text("hello"),Tag("/b"),Text(" world"),Tag("/p")]

def test_lex_empty_tag():
    assert lex("<p></p>") == [Tag("p"),Tag("/p")]

def test_lex_multiple_tags():
    assert lex("<p>hello</p><p>world</p>") == [Tag("p"),Text("hello"),Tag("/p"),Tag("p"),Text("world"),Tag("/p")]

# TODO: fix this test so these characters are unescaped
# def test_lex_special_characters():
#     assert lex("<p>&lt;hello&gt;</p>") == "<hello>"