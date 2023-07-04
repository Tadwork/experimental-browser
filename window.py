""" Creates a window that displays the contents of a web page
    https://browser.engineering/graphics.html
"""
import tkinter as tk
from connection import parse_url, request

HSTEP, VSTEP = 13, 18

def strip_html(body:str):
    """ strips html tags from the body of the response and returns the text

    Args:
        body (str): the body of the response

    Returns:
        str: the body of the response without html tags
    """
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

class Browser:
    """ A Browser window
    """
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.window = tk.Tk()
        self.canvas = tk.Canvas(self.window, width=width, height=height)
        self.canvas.pack()

    def load(self, url):
        parsed_url = parse_url(url)
        response = request(parsed_url)

        cursor_x, cursor_y = HSTEP, VSTEP
        for c in strip_html(response.body):
            self.canvas.create_text(cursor_x, cursor_y, text=c)
            cursor_x += HSTEP
            if cursor_x >= self.width - HSTEP:
                cursor_y += VSTEP
                cursor_x = HSTEP
    