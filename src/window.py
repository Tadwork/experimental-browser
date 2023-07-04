""" Creates a window that displays the contents of a web page
    https://browser.engineering/graphics.html
"""
from dataclasses import dataclass

import tkinter as tk
import tkinter.font as tkfont
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
    display_list = []
    cursor_x = HSTEP
    cursor_y = VSTEP
    weight = "normal"
    style = "roman"
    size = 14

    def __init__(self, tokens, browser) -> None:
        self.browser = browser
        for tok in tokens:
            self.token(tok)

    def token(self, tok):
        font = tkfont.Font(
            family="Times New Roman",
            size=self.size,
            weight=self.weight,
            slant=self.style,
        )
        if isinstance(tok, Tag):
            if tok.tag == "b":
                self.weight = "bold"
            elif tok.tag == "/b":
                self.weight = "normal"
            elif tok.tag == "i":
                self.style = "italic"
            elif tok.tag == "/i":
                self.style = "roman"
            elif tok.tag == 'small':
                self.size -= 2
            elif tok.tag == '\small':
                self.size += 2
            elif tok.tag == 'big':
                self.size += 4
            elif tok.tag == '\big':
                self.size -= 4
        if isinstance(tok, Text):
            for word in tok.text.split():
                w = font.measure(word)
                if self.cursor_x + w > self.browser.width - HSTEP:
                    self.cursor_y += font.metrics("linespace") * 1.25
                    self.cursor_x = HSTEP
                self.display_list.append((self.cursor_x, self.cursor_y, word, font))
                # re-add the whitespace
                self.cursor_x += w + font.measure(" ")


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
