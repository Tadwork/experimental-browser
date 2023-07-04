""" Creates a window that displays the contents of a web page
    https://browser.engineering/graphics.html
"""
from dataclasses import dataclass

import tkinter as tk
from src.fonts import get_font
from src.connection import parse_url, request

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


class Layout:
    """The layout engine for the browser"""

    display_list = []
    cursor_x = HSTEP
    cursor_y = VSTEP
    line = []

    def __init__(self, tokens, browser) -> None:
        self.browser = browser
        self.weight = browser.default_font["weight"]
        self.style = browser.default_font["slant"]
        self.family = browser.default_font["family"]
        self.size = browser.default_font["size"]
        for tok in tokens:
            self.token(tok)
        self.flush()

    def tag(self, tok):
        """make changes to the display list based on the tag

        Args:
            tok (str): the token to process
        """
        if tok.tag == "b":
            self.weight = "bold"
        elif tok.tag == "/b":
            self.weight = "normal"
        elif tok.tag == "i":
            self.style = "italic"
        elif tok.tag == "/i":
            self.style = "roman"
        elif tok.tag == "small":
            self.size -= 2
        elif tok.tag == "/small":
            self.size += 2
        elif tok.tag == "big":
            self.size += 4
        elif tok.tag == "/big":
            self.size -= 4
        elif tok.tag.startswith("pre"):
            self.family = "Courier New"
        elif tok.tag == "/pre":
            self.family = "Times New Roman"
            self.flush()
            self.cursor_y += VSTEP
        elif tok.tag == "br":
            self.flush()
        elif tok.tag == "/p":
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

    def token(self, tok):
        if isinstance(tok, Tag):
            self.tag(tok)
        if isinstance(tok, Text):
            self.text(tok)


def lex(body: str):
    """strips html tags from the body of the response and returns the text and tags

    Args:
        body (str): the body of the response

    Returns:
        list: an array of tags and text
    """
    out = []
    text = ""
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
            if text:
                out.append(Text(text))
                text = ""
        elif c == ">":
            in_tag = False
            out.append(Tag(text))
            text = ""
        else:
            text += c
    if not in_tag and text:
        out.append(Text(text))
    return out


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
        text = lex(response.body)
        self.display_list = Layout(text, browser=self).display_list
        self.draw()
