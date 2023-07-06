""" DOM abstraction for html parsing
"""
SELF_CLOSING_TAGS = [
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
]
HEAD_TAGS = [
    "base",
    "basefont",
    "bgsounds",
    "noscript",
    "link",
    "meta",
    "title",
    "style",
    "script",
]

BLOCK_ELEMENTS = [
    "html",
    "body",
    "article",
    "section",
    "nav",
    "aside",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hgroup",
    "header",
    "footer",
    "address",
    "p",
    "hr",
    "pre",
    "blockquote",
    "ol",
    "ul",
    "menu",
    "li",
    "dl",
    "dt",
    "dd",
    "figure",
    "figcaption",
    "main",
    "div",
    "table",
    "form",
    "fieldset",
    "legend",
    "details",
    "summary",
]


def layout_mode(node):
    """utility function to determine which layout mode to use for a particular layout chunk"""
    if isinstance(node, Text):
        return "inline"
    elif node.children:
        if any(
            [
                isinstance(child, Element) and child.tag in BLOCK_ELEMENTS
                for child in node.children
            ]
        ):
            # if any of the children are block elements treat this as a block layout
            # i.e. if a node contains a <p> and <b> tag
            return "block"
        else:
            return "inline"
    else:
        return "block"


class Text:
    """Text node"""

    def __init__(self, text, parent=None):
        self.text = text
        # added for consistency even though text doesn't have children
        self.children = []
        self.parent = parent

    def __repr__(self):
        return repr(self.text)


class Element:
    """Basic HTML element"""

    def __init__(self, tag, attributes, parent=None):
        self.tag = tag
        self.attributes = attributes
        self.children = []
        self.parent = parent

    def __repr__(self):
        return "<" + self.tag + ">"


class HTMLParser:
    """HTML parser that builds a DOM tree from HTML text"""

    def __init__(self, body) -> None:
        self.body = body
        self.unfinished = []

    def get_attributes(self, text):
        """parse attributes from a tag"""
        parts = text.split()
        tag = parts[0].lower()
        attributes = {}
        for part in parts[1:]:
            if "=" in part:
                key, value = part.split("=", 1)
                # strip outer quotes if they exist
                if len(value) > 2 and value[0] in ["'", '"']:
                    value = value[1:-1]
                attributes[key.lower()] = value
            else:
                attributes[part.lower()] = ""
        return tag, attributes

    def implicit_tags(self, tag):
        """handle malformed HTML by looping through
        the unfinished tags and adding implicit tags like html, head, body, etc.

        Args:
            tag (str): lowercased tag name
        """
        while True:
            open_tags = [node.tag for node in self.unfinished]
            # add the <html> tag if it's missing
            if open_tags == [] and tag != "html":
                self.add_tag("html")
            # add the <head> or <body> tag if it's missing
            elif open_tags == ["html"] and tag not in ["head", "body", "/html"]:
                if tag in HEAD_TAGS:
                    self.add_tag("head")
                else:
                    self.add_tag("body")
            # add the closing </head> tag if it's missing
            elif open_tags == ["html", "head"] and tag not in ["/head"] + HEAD_TAGS:
                self.add_tag("/head")
            else:
                break

    def add_text(self, text: str):
        """adds text to the current unfinished element"""
        # skip whitespace text
        if text.isspace():
            return
        self.implicit_tags(None)
        parent = self.unfinished[-1]
        node = Text(text, parent)
        parent.children.append(node)

    def close_element(self):
        """close the last unfinished element and add it to its parent's children"""
        node = self.unfinished.pop()
        parent = self.unfinished[-1]
        parent.children.append(node)

    def add_tag(self, tag):
        """adds a tag to the current unfinished element"""
        tag, attributes = self.get_attributes(tag)
        if tag.startswith("!"):
            # throw away comments
            return
        self.implicit_tags(tag)
        if tag.startswith("/"):
            # the last tag is an edge case since
            # there aren't any unfinished nodes to add it to
            if len(self.unfinished) == 1:
                return
            self.close_element()
        elif tag in SELF_CLOSING_TAGS:
            # create a new element and append it directly to children
            parent = self.unfinished[-1]
            node = Element(tag, attributes, parent)
            parent.children.append(node)
        else:
            # create a new element and add it to unfinished
            # make sure to account for the first element
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag, attributes, parent)
            self.unfinished.append(node)

    def finish(self):
        """finishes the parse and returns the root node"""
        if len(self.unfinished) == 0:
            self.add_tag("html")
        while len(self.unfinished) > 1:
            self.close_element()
        return self.unfinished.pop()

    def parse(self):
        """strips html tags from the body of the response and returns the text and tags

        Args:
            body (str): the body of the response

        Returns:
            list: an array of tags and text
        """
        text = ""
        in_tag = False
        for c in self.body:
            if c == "<":
                in_tag = True
                if text:
                    self.add_text(text)
                    text = ""
            elif c == ">":
                in_tag = False
                self.add_tag(text)
                text = ""
            else:
                text += c
        if not in_tag and text:
            self.add_text(text)
        return self.finish()


if __name__ == "__main__":
    html = """ 
    <p><b>hello</b> world</p>
    """

    def print_tree(node, indent=0):
        print(" " * indent, node)
        for child in node.children:
            print_tree(child, indent + 2)

    root = HTMLParser(html).parse()
    print_tree(root)
