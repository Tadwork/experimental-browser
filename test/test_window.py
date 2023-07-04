import pytest

from src.window import lex

def test_lex_no_tags():
    assert lex("hello world") == "hello world"

def test_lex_single_tag():
    assert lex("<p>hello world</p>") == "hello world"

def test_lex_nested_tags():
    assert lex("<p><b>hello</b> world</p>") == "hello world"

def test_lex_empty_tag():
    assert lex("<p></p>") == ""

def test_lex_multiple_tags():
    assert lex("<p>hello</p><p>world</p>") == "helloworld"

# TODO: fix this test so these characters are unescaped
# def test_lex_special_characters():
#     assert lex("<p>&lt;hello&gt;</p>") == "<hello>"