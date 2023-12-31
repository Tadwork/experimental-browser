"""CSS Parser"""
import logging

from .dom import Element


logger = logging.getLogger(name="root")


INHERITED_PROPERTIES = {
    "font-family": "Times New Roman",
    "font-size" : "14px",
    "font-style" : "normal",
    "font-weight" : "normal",
    "color" : "black",
    "white-space": "normal"
}

def cascade_priority(rule):
    """sort the rules by priority"""
    selector, _ = rule
    return selector.priority

class CSSParser:
    """recursive descent parser for css files"""

    def __init__(self, s):
        self.s = s
        self.i = 0

    def whitespace(self):
        """skip whitespace"""
        while self.i < len(self.s) and self.s[self.i].isspace():
            self.i += 1
        if self.i < len(self.s) and self.s[self.i] == "@":
            self.i +=1
            word = self.word()
            section_rules = self.parse(abort_char='}')
            logger.debug('skipping @%s directive', word)
                
    def word(self):
        """increment through alphanumeric characters and return a word"""
        start = self.i
        if self.i < len(self.s) and self.s[start] == "'":
            self.i += 1
            while self.i < len(self.s) and not self.s[self.i] in "';\n":
                self.i += 1
            self.i += 1
            return self.s[start+1: self.i-1]
        while self.i < len(self.s):
            if self.s[self.i].isalnum() or self.s[self.i] in "#-.%":
                self.i += 1
            else:
                break
        assert self.i > start
        return self.s[start : self.i]

    def literal(self, literal):
        """increment through a literal string"""
        assert self.i < len(self.s) and self.s[self.i] == literal
        self.i += 1

    def pair(self):
        """parse and return a key value pair
            representing a css property and value

        Returns:
            str, str: a key value pair
        """
        prop = self.word()
        self.whitespace()
        self.literal(":")
        self.whitespace()
        val = self.word()
        return prop.lower(), val

    def body(self):
        """parse and return a dictionary of css properties and values"""
        pairs = {}
        while self.i < len(self.s) and self.s[self.i] != "}":
            try:
                prop, val = self.pair()
                # pairs[prop.lower()] =  THE lower IS EXTRA
                pairs[prop] = val
                self.whitespace()
                self.literal(";")
                self.whitespace()
            except AssertionError:
                why = self.ignore_until([";", "}"])
                if why == ";":
                    self.literal(";")
                    self.whitespace()
                else:
                    break

        return pairs

    def ignore_until(self, chars):
        """increment through the string until a character is found"""
        while self.i < len(self.s):
            if self.s[self.i] in chars:
                return self.s[self.i]
            else:
                self.i += 1

    def selector(self):
        """increment through and find the selector"""
        out = TagSelector(self.word().lower())
        self.whitespace()
        while self.i < len(self.s) and self.s[self.i] != "{":
            tag = self.word()
            descendant = TagSelector(tag.lower())
            out = DescendantSelector(out, descendant)
            self.whitespace()
        return out

    def parse(self, abort_char=None):
        """parse the css file"""
        rules = []
        while self.i < len(self.s):
            try:
                self.whitespace()
                if abort_char and self.s[self.i] == abort_char:
                    break
                selector = self.selector()
                self.literal("{")
                self.whitespace()
                body = self.body()
                self.literal("}")
                rules.append((selector, body))
            except AssertionError:
                # skip the entire selector
                why = self.ignore_until("}")
                if why == "}":
                    self.literal("}")
                    self.whitespace()
                else:
                    break
        return rules


class TagSelector:
    """Matches a tag like a,p, span etc."""

    def __init__(self, tag) -> None:
        self.tag = tag
        self.priority = 1

    def matches(self, node) -> bool:
        """does the selector match the current Tag"""
        return isinstance(node, Element) and self.tag == node.tag


class DescendantSelector:
    """applies the style to all descendants of a tag"""
    def __init__(self, ancestor, descendant) -> None:
        self.ancestor = ancestor
        self.descendant = descendant
        self.priority = ancestor.priority + descendant.priority

    def matches(self, node) -> bool:
        """ recursively check if the selector matches the parent node"""
        if not self.descendant.matches(node):
            return False
        while node.parent:
            if self.ancestor.matches(node.parent):
                return True
            node = node.parent
        return False
