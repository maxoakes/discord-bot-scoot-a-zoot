from state import MessageType, Utility

class Quote:
    quote: str
    author: str
    time_place: str

    def __init__(self, quote_text: str, author_name: str, time_place: str):
        self.quote = quote_text
        self.author = author_name
        self.time_place = time_place
    
    def get_embed(self):
        import discord
        embed = discord.Embed(title="Quote", color=MessageType.QUOTE.value)
        embed.description = self.quote
        embed.add_field(name="Author", value=self.author, inline=True)
        embed.add_field(name="Time/Place", value=self.time_place, inline=True)
        return embed
    
    def get_markdown_string(self):
        full_text = self.quote
        if Utility.is_null_or_whitespace(self.author):
            full_text = f"{full_text}"
        else:
            full_text = f"{full_text} -**{self.author}**"
        if not Utility.is_null_or_whitespace(self.time_place):
            full_text = f"{full_text},  {self.time_place}"
        return full_text


    def as_dict(self):
        return {
            "quote": self.quote,
            "author": self.author,
            "time_place": self.time_place
        }
    

    def __str__(self):
        full_text = self.quote
        if Utility.is_null_or_whitespace(self.author):
            full_text = f"{full_text} -Unknown"
        else:
            full_text = f"{full_text} -{self.author}"
        if not Utility.is_null_or_whitespace(self.time_place):
            full_text = f"{full_text},  {self.time_place}"
        return full_text
    

    def parse_from_raw(input: str):
        if Utility.is_null_or_whitespace(input):
            return ""
        
        # quote elements
        quote_text: str
        author: str
        time_place: str

        # parse text
        quote_type = input[0]
        last_quotation = input.rfind(quote_type)
        quote_text = input[:last_quotation+1]

        # parse author and time/place
        metadata = input[last_quotation+1:]
        metadata_start_position = 0
        for i, c in enumerate(metadata):
            if c.isdigit() or c.isalpha():
                metadata_start_position = i
                break
        
        metadata = metadata[metadata_start_position:]

        end_position = metadata.find(",")
        # if -1, then metadata=author
        if end_position > 0:
            author = metadata[:end_position]
            time_place = metadata[end_position+1:].strip()
        else:
            author = metadata
            time_place = ""

        quote_text = quote_text.strip()
        author = author.strip()
        time_place = time_place.strip()
        
        return Quote(quote_text, author, time_place)