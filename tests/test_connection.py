import pytest
from src.connection import parse_url

def test_parse_url_http():
    url = "http://www.example.com/path/to/resource"
    result = parse_url(url)
    assert result.scheme == "http"
    assert result.host == "www.example.com"
    assert result.port == 80
    assert result.path == "/path/to/resource"

def test_parse_url_https():
    url = "https://www.example.com/path/to/resource"
    result = parse_url(url)
    assert result.scheme == "https"
    assert result.host == "www.example.com"
    assert result.port == 443
    assert result.path == "/path/to/resource"

def test_parse_url_with_port():
    url = "http://www.example.com:8080/path/to/resource"
    result = parse_url(url)
    assert result.scheme == "http"
    assert result.host == "www.example.com"
    assert result.port == 8080
    assert result.path == "/path/to/resource"

def test_parse_url_no_path():
    url = "http://www.example.com"
    result = parse_url(url)
    assert result.scheme == "http"
    assert result.host == "www.example.com"
    assert result.port == 80
    assert result.path == "/"

def test_parse_url_invalid_url():
    with pytest.raises(ValueError):
        parse_url("not a url")
        