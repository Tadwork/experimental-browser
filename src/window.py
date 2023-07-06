""" Creates a window that displays the contents of a web page
    https://browser.engineering/graphics.html
"""

import tkinter as tk
from src.fonts import get_font
from src.dom import HTMLParser
from src.connection import parse_url, request
from src.layout import DocumentLayout

HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100

class Browser:
    """A Browser window"""

    display_list = []
    nodes = None
    scroll_start = 0

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.window = tk.Tk()
        self.window.title("Browser")
        self.window.bind("<Down>", self.scroll)
        self.window.bind("<Up>", self.scroll)
        self.canvas = tk.Canvas(self.window, width=width, height=height)
        self.default_font = get_font("Times New Roman", 14, "normal", "roman")
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

    def draw(self):
        """draw the display list on the canvas"""
        self.canvas.delete("all")
        for x, y, word, font in self.display_list:
            if y > self.scroll_start + self.height:
                continue
            if y + VSTEP < self.scroll_start:
                continue
            self.canvas.create_text(
                x, y - self.scroll_start, text=word, font=font, anchor="nw"
            )

    def load(self, url):
        """load a url into the browser

        Args:
            url (URL): the url to load
        """
        parsed_url = parse_url(url)
        if parsed_url.scheme in ["http", "https"]:
            response = request(parsed_url)
            self.nodes = HTMLParser(response.body).parse()
        elif parsed_url.scheme == "file":
            with open(
                parsed_url.host + "/" + parsed_url.path, encoding="utf-8"
            ) as file:
                html = file.read()
                self.nodes = HTMLParser(html).parse()
        document = DocumentLayout(self.nodes, browser=self)
        document.layout()
        self.display_list = []
        document.paint(self.display_list)
        self.draw()
