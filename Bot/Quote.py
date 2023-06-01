from Util import MessageType


class Quote:
    __quote: str
    __author: str
    __location: str
    __time: str
    __creator: str

    def __init__(self, creator, perform_parse=False, raw='', quote='<No content>', author='Anonymous', location=None, time=None):
        self.__creator = creator
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
    
    def get_embed(self):
        import discord
        embed = discord.Embed(title="Quote (without quotation marks)", color=MessageType.QUOTE.value)
        embed.add_field(name="Text", value=self.__quote, inline=False)
        embed.add_field(name="Author", value=self.__author, inline=True)
        embed.add_field(name="Location", value=self.__location, inline=True)
        embed.add_field(name="Time", value=self.__time, inline=True)
        embed.set_footer(text=f"Added by {self.__creator}")
        return embed
    
    def __str__(self):
        return self.get_quote_formal()