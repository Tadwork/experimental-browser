""" Creates a window that displays the contents of a web page
    https://browser.engineering/graphics.html
"""

import tkinter as tk
from src.fonts import get_font
from src.dom import HTMLParser, Text
from src.connection import parse_url, request

HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100

class Layout:
    """The layout engine for the browser"""

    display_list = []
    cursor_x = HSTEP
    cursor_y = VSTEP
    line = []

    def __init__(self, nodes, browser) -> None:
        self.browser = browser
        self.weight = browser.default_font["weight"]
        self.style = browser.default_font["slant"]
        self.family = browser.default_font["family"]
        self.size = browser.default_font["size"]
        self.walk_html(nodes)
        self.flush()

    def open_tag(self, tag):
        """make changes to the display list based on the tag

        Args:
            tag (str): the tag to process
        """
        if tag == "b":
            self.weight = "bold"
        elif tag == "i":
            self.style = "italic"
        elif tag == "small":
            self.size -= 2
        elif tag == "big":
            self.size += 4
        elif tag == "pre":
            self.family = "Courier New"
        elif tag == "br":
            self.flush()
        
    def close_tag(self, tag):
        """make changes to the display list based on the tag

        Args:
            tag (str): the tag to process
        """
        if tag == "b":
            self.weight = self.browser.default_font["weight"]
        elif tag == "i":
            self.style = self.browser.default_font["slant"]
        elif tag == "small":
            self.size += 2
        elif tag == "big":
            self.size -= 4
        elif tag == "pre":
            self.family = self.browser.default_font["family"]
            self.flush()
            self.cursor_y += VSTEP
        elif tag == "br":
            self.flush()
        elif tag == "p":
            self.flush()
            self.cursor_y += VSTEP

    def text(self, tok):
        """adds text to the display list"""
        font = get_font(self.family, self.size, self.weight, self.style)
        for word in tok.text.split():
            w = font.measure(word)
            if self.cursor_x + w > self.browser.width - HSTEP:
                self.flush()
            self.line.append((self.cursor_x, word, font))
            # add the width of the word and a space
            self.cursor_x += w + font.measure(" ")

    def walk_html(self, node):
        if isinstance(node, Text):
            self.text(node)
        else:
            self.open_tag(node.tag)
            for child in node.children:
                self.walk_html(child)
            self.close_tag(node.tag)
            
    def flush(self):
        """flush the current line to the display list"""
        if not self.line:
            return
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent
        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))
        self.cursor_x = HSTEP
        self.line = []
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent


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
        response = request(parsed_url)
        self.nodes = HTMLParser(response.body).parse()
        self.display_list = Layout(self.nodes, browser=self).display_list
        self.draw()
