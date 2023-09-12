""" Creates a window that displays the contents of a web page
    https://browser.engineering/graphics.html
"""
from dataclasses import dataclass
import tkinter as tk
import tkinter.font as tkfont
import logging

from src.tree_utils import tree_to_list
from .css import INHERITED_PROPERTIES, CSSParser, cascade_priority
from .dom import HTMLParser, Element
from .connection import parse_url, request, resolve_url
from .layout import DocumentLayout
import time

HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100

@dataclass
class WebFont:
    font: tkfont.Font
    whitespace: int
    
class Browser:
    """A Browser window"""

    display_list = []
    nodes = None
    scroll_start = 0
    document = None
    fonts = {}
    log = logging.getLogger(name="root")
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.window = tk.Tk()
        self.window.title("Browser")
        self.window.bind("<Down>", self.scroll)
        self.window.bind("<Up>", self.scroll)
        self.canvas = tk.Canvas(self.window, width=width, height=height, bg="white")
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
    
    def get_font(self, family: str, size: int, weight: str, slant: str) -> WebFont:
        """_summary_

        Args:
            family (str): The font family
            size (int): The font size 
            weight (str): "normal" or "bold"
            slant (str): "roman" or "italic"

        Returns:
            font: a font object
        """
        key = (family, size, weight, slant)
        if key not in self.fonts:
            font = tkfont.Font(
                family=family,
                size=size,
                weight=weight,
                slant=slant,
            )
            # create a dummy widget to load the font into tk for performance
            tk.Label(self.window, text=" ", font=font)
            self.fonts[key] = WebFont(font, whitespace=font.measure(" "))
        return self.fonts[key]
    
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
        # inherit from parent before applying explicit styles
        for prop, default_value in INHERITED_PROPERTIES.items():
            if node.parent:
                node.style[prop] = node.parent.style.get(prop, default_value)
            else:
                node.style[prop] = default_value
        if isinstance(node, Element) and "style" in node.attributes:
            pairs = CSSParser(node.attributes["style"]).body()
            for prop,val in pairs.items():
                node.style[prop] = val
        for selector, body in rules:
            if not selector.matches(node):
                continue
            
            for prop, value in body.items():
                node.style[prop] = value
        if node.style["font-size"].endswith("%"):
            if node.parent:
                parent_font_size = node.parent.style["font-size"]
            else:
                parent_font_size = INHERITED_PROPERTIES["font-size"]
            # everything but the %
            node_pct = float(node.style["font-size"][:-1]) / 100
            # everything but the px
            parent_px = float(parent_font_size[:-2])
            # convert to a fixed value
            node.style["font-size"] = str(node_pct * parent_px) + "px"
        for child in node.children:
            self.style(child, rules)
            
    def load(self, url):
        """load a url into the browser

        Args:
            url (URL): the url to load
        """
        parsed_url = parse_url(url)
        _, body = request(parsed_url)
        self.nodes = HTMLParser(body).parse()

        # CSS
        rules = self.default_style_sheet.copy()
        links = [ node.attributes["href"] for node in tree_to_list(self.nodes, []) 
                 if isinstance(node, Element)
                 and node.tag == "link"
                 and "href" in node.attributes
                 and node.attributes.get("rel") == "stylesheet"]
        for link in links:
            try:
                _, body = request(parse_url(resolve_url(link,url)))
            except:
                continue
            rules.extend(CSSParser(body).parse())
        self.style(self.nodes, sorted(rules,key=cascade_priority))
        # Layout
        
        self.document = DocumentLayout(self.nodes, browser=self)
        # t1 = time.perf_counter(), time.process_time()
        self.document.layout()
        # t2 = time.perf_counter(), time.process_time()
        self.display_list = []
        self.document.paint(self.display_list)
        self.draw()
        
        # print(f'Real Time: {t2[0] - t1[0]:.2f} seconds')
        # print(f'Real Time: {t2[1] - t1[1]:.2f} seconds')
