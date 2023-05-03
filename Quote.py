class Quote:
    quote: str = None
    author: str = None
    location: str = None
    time: str = None

    def __init__(self, quote=None, author=None, location=None, time=None):
        self.quote = quote
        self.author = author
        self.location = location
        self.time = time
    
    def get_quote_short(self):
        return f'"{self.quote}" -*{self.author}*'
    def __str__(self):
        after_quote = ""
        if not self.location and self.time:
            after_quote = f", {self.time}"
        elif self.location and not self.time:
            after_quote = f" in {self.location}"
        elif self.location and self.time:
            after_quote = f", {self.time} in {self.location}"
        return f'"{self.quote}" -*{self.author}{after_quote}*'