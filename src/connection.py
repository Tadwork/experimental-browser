""" utilities for making http requests
"""
from dataclasses import dataclass,field
import socket
import ssl
from typing import Any

@dataclass
class Status:
    """
    A wrapper for an HTTP status code
    """
    code: int
    explanation: str
    def __str__(self):
        return f"{self.code} {self.explanation}"
    def __repr__(self):
        return f"Status({self.code}, {self.explanation})"
    
@dataclass
class Response:
    """ A wrapper for an HTTP response
    
        version (str): the http version
        status (Status): the status code and explanation
        headers (dict): the headers
        body (str): the body of the response
    """
    version: str
    status: field(default_factory=lambda: Status(200, "OK"))
    headers: dict = field(default_factory=dict)
    body: str = field(default_factory=str)

@dataclass
class URL:
    """ wrapper for a url
    """
    scheme: str
    host: str
    port: int
    path: str

def parse_url(url:str):
    """ parses a url into its components

    Args:
        url (str): url to parse

    Returns:
        URL: a URL object
    """
    scheme, url = url.split("://", 1)
    if url.count("/") == 0:
        url += "/"
    host,path = url.split("/",1)
    path = "/" + path  # add back the leading slash
    port = 443 if scheme == "https" else 80
    if ":" in host:
        host, p = host.split(":", 1)
        port = int(p)
    return URL(scheme, host, port, path)

def get_page(sock:Any,url:URL):
    """ uses a socket to get a page

    Args:
        sock (Any): a socket
        url (URL): the url to get

    Returns:
        
    """
    sock.connect((url.host, url.port))
    sock.send(
        f"GET {url.path} HTTP/1.0\r\n".encode("utf8") +
        f"Host: {url.host}\r\n\r\n".encode("utf8")
        )
    response = sock.makefile("r", encoding="utf8", newline="\r\n")
    status_line = response.readline()
    version, status, explanation = status_line.split(" ", 2)
    assert status == "200", f"{status}: {explanation}"
    headers = {}
    while True:
        line = response.readline()
        if line == "\r\n":
            break
        header, value = line.split(":", 1)
        headers[header.lower()] = value.strip()
    assert "transfer-encoding" not in headers
    assert "content-encoding" not in headers
    body = response.read()
    return Response(version, Status(status, explanation), headers, body)

def request(url:URL):
    """ makes an http request

    Args:
        url (URL): the url to request

    Returns:
        Response: an HTTP response
    """
    assert url.scheme in ("http", "https"), f"Unknown scheme {url.scheme}"
    with socket.socket(
        family=socket.AF_INET,
        type=socket.SOCK_STREAM,
        proto=socket.IPPROTO_TCP,
    ) as sock:
        if url.scheme == "https":
            ctx = ssl.create_default_context()
            with ctx.wrap_socket(sock, server_hostname=url.host) as secure_sock:
                return get_page(secure_sock,url)
        elif url.scheme == "http":
            return get_page(sock,url)