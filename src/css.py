"""CSS Parser"""

class CSSParser:
    """recursive descent parser for css files"""
    def __init__(self,s):
        self.s = s
        self.i = 0
    
    def whitespace(self):
        """skip whitespace"""
        while self.i < len(self.s) and self.s[self.i].isspace():
            self.i += 1
    
    def word(self):
        """increment through alphanumeric characters and return a word"""
        start = self.i
        while self.i < len(self.s):
            if self.s[self.i].isalnum() or self.s[self.i] in "#-.%":
                self.i += 1
            else:
                break
        assert self.i > start
        return self.s[start:self.i]
    
    def literal(self,literal):
        """increment through a literal string"""
        assert self.i < len(self.s) and self.s[self.i] == literal
        self.i += 1
        
    def pair(self):
        """ parse and return a key value pair
            representing a css property and value

        Returns:
            str, str: a key value pair 
        """
        prop=self.word()
        self.whitespace()
        self.literal(":")
        self.whitespace()
        val = self.word()
        return prop.lower(), val
    
    def body(self):
        """parse and return a dictionary of css properties and values"""
        pairs = {}
        while self.i < len(self.s):
            try:
                prop, val = self.pair()
                # pairs[prop.lower()] =  THE lower IS EXTRA  
                pairs[prop] = val
                self.whitespace()
                self.literal(";")
                self.whitespace()
            except AssertionError:
                why = self.ignore_until(";")
                if why == ";":
                    self.literal(";")
                    self.whitespace()
                else:
                    break
                
        return pairs
    
    def ignore_until(self,chars):
        """increment through the string until a character is found"""
        while self.i < len(self.s):
            if self.s[self.i] in chars:
                return self.s[self.i]
            else:
                self.i += 1
    
    