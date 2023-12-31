""" A module that represents the layout tree in the browser"""
import html

from .dom import Text, layout_mode

HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100


class DrawText:
    """abstraction for drawing text on the canvas"""

    def __init__(self, x, y, text, font, color):
        self.top = y
        self.left = x
        self.text = text
        self.font = font
        self.bottom = y + font.metrics("linespace")
        self.color = color

    def execute(self, scroll, canvas):
        """draw the text"""
        canvas.create_text(
            self.left, self.top - scroll, text=self.text, 
            font=self.font, fill=self.color, anchor="nw"
        )


class DrawRect:
    """abstraction for drawing a rectangle on the canvas"""

    def __init__(self, x1, y1, x2, y2, color) -> None:
        self.top = y1
        self.left = x1
        self.bottom = y2
        self.right = x2
        self.color = color

    def execute(self, scroll, canvas):
        """draw the rectangle"""
        canvas.create_rectangle(
            self.left,
            self.top - scroll,
            self.right,
            self.bottom - scroll,
            # border width to 0 to make it invisible
            width=0,
            fill=self.color,
        )


class DocumentLayout:
    """A special type of layout representing the document"""
    display_list = []

    def __init__(self, node, browser) -> None:
        self.node = node
        self.parent = None
        self.children = []
        self.browser = browser
        self.width = self.browser.width - 2 * HSTEP
        self.x = HSTEP
        self.y = VSTEP
        self.height = 2 * VSTEP

    def layout(self):
        """create the child and then begin recursively laying out children"""
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

    def layout(self):
        """layout all the block and inline elements in this node"""
        # t1 = time.perf_counter(), time.process_time()
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
            self.line = []
            self.walk_html(self.node)
            self.flush()
        for child in self.children:
            child.layout()
        if mode == "block":
            self.height = sum([child.height for child in self.children])
        else:
            self.height = self.cursor_y
        # t2 = time.perf_counter(), time.process_time()
        # print(f'Real Time: {t2[0] - t1[0]:.2f}s | process Time: {t2[1] - t1[1]:.2f}s')

    def paint(self, display_list):
        """paint the display list

        Args:
            display_list (List): list of DrawText and DrawRect objects
        """
        bgcolor = self.node.style.get("background-color", "transparent")
        if bgcolor != "transparent":
            x2, y2 = self.x + self.width, self.y + self.height
            rect = DrawRect(self.x, self.y, x2, y2, bgcolor)
            display_list.append(rect)

        for child in self.children:
            child.paint(display_list)

        for x, y, word, font,color in self.display_list:
            #TODO: should this be
            # display_list.append(DrawText(self.x + x, self.y + y, word, font, color))
            display_list.append(DrawText(x, y, word, font, color))
            
    def get_font(self, node):
        "get the font for this node"
        weight = node.style["font-weight"]
        style = node.style["font-style"]
        if style == "normal":
            style = "roman"
        size =  int(float(node.style["font-size"][:-2]) * .75)
        return self.browser.get_font(node.style["font-family"], size,weight,style)
    
    def text(self, node):
        """adds text to the display list"""
        color = node.style["color"]
        font = self.get_font(node)
        for word in node.text.split():
                word = html.unescape(word)
                w = font.font.measure(word)
                if self.cursor_x + w > self.width:
                    self.flush()
                self.line.append((self.cursor_x, word, font.font, color))
                # add the width of the word and a space
                self.cursor_x += w + font.whitespace

    def walk_html(self, node):
        """walk the html tree"""
        if isinstance(node, Text):
            self.text(node)
        else:
            if node.tag == "br":
                self.flush()
            for child in node.children:
                self.walk_html(child)

    def flush(self):
        """flush the current line to the display list"""
        if not self.line:
            return
        metrics = [font.metrics() for x, word, font, _ in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent
        for rel_x, word, font, color in self.line:
            x = self.x + rel_x
            y = self.y + baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font, color))
        self.cursor_x = 0
        self.line = []
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent
