class Quote:
    __quote: str = None
    __author: str = "Anonymous"
    __location: str = None
    __time: str = None

    def __init__(self, perform_parse=False, raw='', quote=None, author=None, location=None, time=None):
        if perform_parse:
            quote_type = '"'
            first_index = -1
            for q in ["'", '"', '`']:
                first_index = raw.find(q)
                quote_type = q
                if first_index != -1:
                    break
            if first_index == -1:
                # the input quote is bad
                return
            quote_parts = raw.split(quote_type)[1:]
            self.__quote = quote_parts[0].strip()
            if quote_parts[1].find(',') == -1:
                self.__author = quote_parts[1].replace('-','').strip()
            else:
                # should be in format <author>, <time>, <location>
                metadata = quote_parts[1].split(',')
                try:
                    self.__author = metadata[0].replace('-','').strip()
                except:
                    pass
                try:
                    self.__time = metadata[1].strip()
                except:
                    pass
                try:
                    self.__location = metadata[2].strip()
                except:
                    pass
        else:
            self.__quote = quote
            self.__author = author
            self.__location = location
            self.__time = time
    
    def is_bad(self):
        return self.__quote == None
    def get_quote_short(self):
        return f'"{self.__quote}" -*{self.__author}*'
    
    def get_quote_formal(self):
        after_quote = ""
        if not self.__location and self.__time:
            after_quote = f", {self.__time}"
        elif self.__location and not self.__time:
            after_quote = f" in {self.__location}"
        elif self.__location and self.__time:
            after_quote = f", {self.__time} in {self.__location}"
        return f'"{self.__quote}" -*{self.__author}{after_quote}*'
    
    # includes markdown
    def get_quote_verbose(self):
        return f"Quote Text w/o quotation: `{self.__quote}`\nAuthor: `{self.__author}`\nLocation: `{self.__location}`\nTime:`{self.__time}`"
    
    def __str__(self):
        return self.get_quote_formal()