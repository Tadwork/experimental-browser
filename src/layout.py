
from src.fonts import get_font
from src.dom import Text, layout_mode

HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100

class DocumentLayout:
    display_list = []
    """A special type of layout representing the document"""

    def __init__(self, node, browser) -> None:
        self.node = node
        self.parent = None
        self.children = []
        self.browser = browser

    def layout(self):
        """create the child and then begin recursively laying out children

        Args:
            browser (Browser): the browser to get window dimensions
        """
        child = BlockLayout(self.node, self, None, self.browser)
        self.children.append(child)
        self.width = self.browser.width - 2 * HSTEP
        self.x = HSTEP
        self.y = VSTEP
        child.layout()
        self.height = child.height + 2 * VSTEP
        
    def paint(self, display_list):
        self.children[0].paint(display_list)


class BlockLayout:
    """A layout abstraction for the browser"""

    display_list = []
    cursor_x = 0
    cursor_y = 0
    line = []
    x = 0
    y = 0

    def __init__(self, node, parent, previous, browser) -> None:
        self.browser = browser
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []
        self.width = self.browser.width
        self.height = self.browser.height
        self.weight = self.browser.default_font["weight"]
        self.style = self.browser.default_font["slant"]
        self.family = self.browser.default_font["family"]
        self.size = self.browser.default_font["size"]

    def layout(self):
        self.width = self.parent.width
        self.x = self.parent.x
        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y
        mode = layout_mode(self.node)
        
        if mode == "block":
            previous = None
            for child in self.node.children:
                next_node = BlockLayout(child, self, previous, self.browser)
                self.children.append(next_node)
                previous = next_node
        else:
            self.display_list = []
            self.cursor_x = 0
            self.cursor_y = 0
            self.weight = self.browser.default_font["weight"]
            self.style = self.browser.default_font["slant"]
            self.family = self.browser.default_font["family"]
            self.size = self.browser.default_font["size"]
            self.line = []
            self.walk_html(self.node)
            self.flush()
        for child in self.children:
            child.layout()
        if mode == "block":
            self.height = sum([child.height for child in self.children])
        else:
            self.height = self.cursor_y
            
    def paint(self, display_list):
        for child in self.children:
            child.paint(display_list)
        display_list.extend(self.display_list)

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

    def text(self, node):
        """adds text to the display list"""
        font = get_font(self.family, self.size, self.weight, self.style)
        for word in node.text.split():
            w = font.measure(word)
            if self.cursor_x + w > self.width:
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
        for rel_x, word, font in self.line:
            x = self.x + rel_x
            y = self.y + baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))
        self.cursor_x = 0
        self.line = []
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent