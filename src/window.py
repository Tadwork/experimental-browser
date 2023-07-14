""" Creates a window that displays the contents of a web page
    https://browser.engineering/graphics.html
"""

import tkinter as tk

from src.tree_utils import tree_to_list
from .fonts import get_font
from .css import CSSParser
from .dom import HTMLParser, Element
from .connection import parse_url, request, resolve_url
from .layout import DocumentLayout

HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100

class Browser:
    """A Browser window"""

    display_list = []
    nodes = None
    scroll_start = 0
    document = None

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
        with open("src/browser.css", "r", encoding="utf-8") as file:
            self.default_style_sheet = CSSParser(file.read()).parse()

    def scroll(self, event):
        """scroll the display list

        Args:
            event (dict): a Tkinter window event
        """
        if event.keysym == "Down":
            max_y = self.document.height - self.height
            self.scroll_start = min(self.scroll_start + SCROLL_STEP, max_y)
        elif event.keysym == "Up" and self.scroll_start > 0:
            self.scroll_start -= SCROLL_STEP
        self.draw()

    def draw(self):
        """draw the display list on the canvas"""
        self.canvas.delete("all")
        for cmd in self.display_list:
            if cmd.top > self.scroll_start + self.height:
                continue
            if cmd.bottom < self.scroll_start:
                continue
            cmd.execute(self.scroll_start, self.canvas)

    def style(self,node, rules):
        """parse the style attribute of a node"""
        node.style = {}
        if isinstance(node, Element) and "style" in node.attributes:
            pairs = CSSParser(node.attributes["style"]).body()
            for prop,val in pairs.items():
                node.style[prop] = val
        for selector, body in rules:
            if not selector.matches(node):
                continue
            for prop, value in body.items():
                node.style[prop] = value
        for child in node.children:
            self.style(child, rules)
            
    def load(self, url):
        """load a url into the browser

        Args:
            url (URL): the url to load
        """
        parsed_url = parse_url(url)
        response = request(parsed_url)
        self.nodes = HTMLParser(response.body).parse()

        # CSS
        rules = self.default_style_sheet.copy()
        links = [ node.attributes["href"] for node in tree_to_list(self.nodes, []) 
                 if isinstance(node, Element)
                 and node.tag == "link"
                 and "href" in node.attributes
                 and node.attributes.get("rel") == "stylesheet"]
        for link in links:
            try:
                response = request(resolve_url(link,url))
            except:
                continue
            rules.extend(CSSParser(response.body).parse())
        self.style(self.nodes, rules)
        # Layout
        self.document = DocumentLayout(self.nodes, browser=self)
        self.document.layout()
        self.display_list = []
        self.document.paint(self.display_list)
        self.draw()
