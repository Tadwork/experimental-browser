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

class Layout:
    node = None
    browser = None
    x = 0
    y = 0
    
    def __init__(self, node, browser, parent = None, previous = None) -> None:
        self.node = node
        self.browser = browser
        self.parent = parent
        self.previous = previous
        self.children = []
        self.width = browser.width
        self.height = browser.height
    
    def get_font(self):
        "get the font for this layout's node"
        weight = self.node.style["font-weight"]
        style = self.node.style["font-style"]
        if style == "normal":
            style = "roman"
        size =  int(float(self.node.style["font-size"][:-2]) * .75)
        return self.browser.get_font(self.node.style["font-family"], size,weight,style)
    
    def layout(self):
        pass
    
    def paint(self, display_list):
        pass
    
class DocumentLayout(Layout):
    """A special type of layout representing the document"""
    display_list = []

    def __init__(self, node, browser) -> None:
        super().__init__(node,browser)
        self.width = self.browser.width - 2 * HSTEP
        self.height = 2 * VSTEP

    def layout(self):
        """create the child and then begin recursively laying out children"""
        child = BlockLayout(self.node,self.browser, self, None )
        self.children.append(child)
        self.width = self.browser.width - 2 * HSTEP
        self.x = HSTEP
        self.y = VSTEP
        child.layout()
        self.height = child.height + 2 * VSTEP

    def paint(self, display_list):
        self.children[0].paint(display_list)


class BlockLayout(Layout):
    """A layout abstraction for the browser"""

    display_list = []
    cursor_x = 0
    cursor_y = 0
    line = []
    previous_word = None

    def __init__(self, node,browser, parent, previous) -> None:
        super().__init__(node,browser, parent, previous)

    def layout(self):
        """layout all the block and inline elements in this node"""
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
                next_node = BlockLayout(child, self.browser, self, previous)
                self.children.append(next_node)
                previous = next_node
        else:
            self.new_line()
            self.walk_html(self.node)
        for child in self.children:
            child.layout()
        self.height = sum([child.height for child in self.children])

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
    
    def new_line(self):
        """creates a new line and resets some fields
        """
        self.previous_word = None
        self.cursor_x = 0
        last_line = self.children[-1] if self.children else None
        new_line = LineLayout(self.node, self, last_line, self.browser)
        self.children.append(new_line)
        
    def text(self, node):
        """adds text to the display list"""
        font = self.get_font()
        for word in node.text.split():
                word = html.unescape(word)
                w = font.measure(word)
                if self.cursor_x + w > self.width:
                    self.new_line()
                line = self.children[-1]
                text = TextLayout(node, self.browser, line, self.previous_word, word)
                line.children.append(text)
                self.previous_word = text
                # add the width of the word and a space
                self.cursor_x += w + font.measure(" ")

    def walk_html(self, node):
        """walk the html tree"""
        if isinstance(node, Text):
            self.text(node)
        else:
            for child in node.children:
                self.walk_html(child)

class LineLayout(Layout):
    def __init__(self, node, parent, previous, browser):
        super().__init__(node,browser, parent, previous)
        
    def layout(self):
        self.width = self.parent.width
        self.x = self.parent.x
        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y
        for word in self.children:
            word.layout()
        max_ascent = max([word.font.metrics("ascent") for word in self.children])
        baseline = self.y + 1.25 * max_ascent
        for word in self.children:
            word.y = baseline - word.font.metrics("ascent")
        max_descent = max([word.font.metrics("descent") for word in self.children])
        self.height = 1.25 * (max_ascent + max_descent)
        
    def paint(self, display_list):
        for child in self.children:
            child.paint(display_list)
        
class TextLayout(Layout):
    
    def __init__(self, node, browser, parent, previous, word ):
        super().__init__(node,browser, parent, previous)
        self.word = word
        
    def layout(self):
        self.font = self.get_font()
        self.width = self.font.measure(self.word)
        if self.previous:
            self.x = self.previous.x + self.previous.font.measure(" ") + self.previous.width
        else:
            self.x = self.parent.x
        self.height = self.font.metrics("linespace")
    
    def paint(self, display_list):
        color = self.node.style["color"]
        display_list.append(
            DrawText(self.x, self.y, self.word, self.font, color)
        )
