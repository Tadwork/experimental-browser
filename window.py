""" Creates a window that displays the contents of a web page
    https://browser.engineering/graphics.html
"""
from dataclasses import dataclass

import tkinter as tk
import tkinter.font as tkfont
from connection import parse_url, request

HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100

@dataclass
class Text:
    """A wrapper for text to display"""
    text: str
    
@dataclass
class Tag:
    """A wrapper for html tags"""
    tag: str
    attributes: dict = None


def lex(body: str):
    """strips html tags from the body of the response and returns the text

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
    """A Browser window"""

    display_list = []
    scroll_start = 0

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.window = tk.Tk()
        self.window.title("Browser")
        self.window.bind("<Down>", self.scroll)
        self.window.bind("<Up>", self.scroll)
        self.canvas = tk.Canvas(self.window, width=width, height=height)
        self.canvas.pack()

    def scroll(self, event):
        """scroll the display list

        Args:
            event (dict): a Tkinter window event
        """
        if event.keysym == "Down":
            self.scroll_start += SCROLL_STEP
        elif event.keysym == "Up" and self.scroll_start > 0:
            self.scroll_start -= SCROLL_STEP
        self.draw()

    def layout(self, text):
        """generate a layout list from the text

        Args:
            text (str): the text to layout

        Returns:
            list: list of tuples of the form (x, y, c)
            where x and y are the coordinates of the character c
        """
        tnr_font = tkfont.Font(family="Times New Roman", size=14)
        display_list = []
        cursor_x, cursor_y = HSTEP, VSTEP
        for word in text.split():
            w = tnr_font.measure(word)
            if cursor_x + w > self.width - HSTEP:
                cursor_y += tnr_font.metrics("linespace") * 1.25
                cursor_x = HSTEP
            display_list.append((cursor_x, cursor_y, word))
            #readd the whitespace
            cursor_x += w + tnr_font.measure(" ")
        return display_list

    def draw(self):
        """draw the display list on the canvas"""
        self.canvas.delete("all")
        for x, y, c in self.display_list:
            if y > self.scroll_start + self.height:
                continue
            if y + VSTEP < self.scroll_start:
                continue
            self.canvas.create_text(x, y - self.scroll_start, text=c , anchor="nw")

    def load(self, url):
        """ load a url into the browser

        Args:
            url (URL): the url to load
        """
        parsed_url = parse_url(url)
        response = request(parsed_url)
        text = lex(response.body)
        self.display_list = self.layout(text)
        self.draw()
