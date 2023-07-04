""" utilities for making http requests
"""
import socket
import ssl

def parse_url(url:str):
    """ parses a url into its components

    Args:
        url (str): url to parse

    Returns:
        scheme (str): http or https
        host (str): the host name
        port (int): the port number
        path (str): the rest of the path starting from /
    """
    scheme, url = url.split("://", 1)
    assert scheme in ("http", "https"), f"Unknown scheme {scheme}"
    host,path = url.split("/",1)
    path = "/" + path  # add back the leading slash
    port = 443 if scheme == "https" else 80
    if ":" in host:
        host, p = host.split(":", 1)
        port = int(p)
    return scheme, host, port, path

def get_page(sock:str,host:str,port:int,path:str):
    """ uses a socket to get a page

    Args:
        sock (str): the socket to use
        host (str): the host name
        port (int): the port number
        path (str): the rest of the path 

    Returns:
        version (str): the http version
        status (str): the status code
        explanation (str): the explanation of the status code
        headers (dict): the headers
        body (str): the body of the response
    """
    sock.connect((host, port))
    sock.send(
        f"GET {path} HTTP/1.0\r\n".encode("utf8") +
        f"Host: {host}\r\n\r\n".encode("utf8")
        )
    response = sock.makefile("r", encoding="utf8", newline="\r\n")
    statusline = response.readline()
    version, status, explanation = statusline.split(" ", 2)
    assert status == "200", f"{status}: {explanation}"
    headers = {}
    while True:
        line = response.readline()
        if line == "\r\n": break
        header, value = line.split(":", 1)
        headers[header.lower()] = value.strip()
    assert "transfer-encoding" not in headers
    assert "content-encoding" not in headers
    body = response.read()
    return version, status, explanation, headers, body

def request(scheme:str,host:str,port:int,path:str):
    """ makes an http request

    Args:
        scheme (str): http or https
        host (str): the host name
        port (int): port number
        path (str): the rest of the path

    Returns:
        values from get_path
    """
    with socket.socket(
        family=socket.AF_INET,
        type=socket.SOCK_STREAM,
        proto=socket.IPPROTO_TCP,
    ) as sock:
        if scheme == "https":
            ctx = ssl.create_default_context()
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                return get_page(ssock,host,port,path)
        else:
            return get_page(sock,host,port,path)