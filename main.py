import socket
import argparse

# https://browser.engineering/http.html

args = argparse.ArgumentParser()
args.add_argument("--url", help="The URL to download")

def parse_url(url):
    assert url.startswith("http://")
    url = url[len("http://"):]
    host,path = url.split("/",1)
    path = "/" + path  # add back the leading slash
    return host, path

def request(host,path):
    s = socket.socket(
        family=socket.AF_INET,
        type=socket.SOCK_STREAM,
        proto=socket.IPPROTO_TCP,
    )
    s.connect((host, 80))
    s.send("GET {} HTTP/1.0\r\n".format(path).encode("utf8") + 
    "Host: {}\r\n\r\n".format(host).encode("utf8"))
    response = s.makefile("r", encoding="utf8", newline="\r\n")
    statusline = response.readline()
    version, status, explanation = statusline.split(" ", 2)
    assert status == "200", "{}: {}".format(status, explanation)
    headers = {}
    while True:
        line = response.readline()
        if line == "\r\n": break
        header, value = line.split(":", 1)
        headers[header.lower()] = value.strip()
    assert "transfer-encoding" not in headers
    assert "content-encoding" not in headers
    body = response.read()
    s.close()
    return version, status, explanation, headers, body
    
def display(body):
    text = []
    in_angle = False
    for c in body:
        if c == "<":
            in_angle = True
        elif c == ">":
            in_angle = False
        elif not in_angle:
            text.append(c)
    return "".join(text)
    
def main():
    url = args.parse_args().url
    host,path = parse_url(url)
    version,status,explanation,headers, body = request(host,path)
    print(display(body))

if __name__ == "__main__":
    main()
