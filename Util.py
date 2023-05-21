import datetime
import threading
from enum import Enum
import discord

class MessageType(Enum):
    FATAL = 0xDC3545 #Red
    NEGATIVE = 0xFFC107 #Orange
    POSITIVE = 0x28A745 #Green
    INFO = 0x17A2B8 #Gray/Blue
    PLAYLIST_ITEM = 0x007BFF #Blue
    PLAYLIST_ALL = 0x007BFF #Blue
    QUOTE = 0x007BFF #Blue

class Util:
    AFFIRMATIVE_RESPONSE = ['y', 'ya', 'ye', 'yea', 'yes', 'yeah', 't', 'true']
    NEGATIVE_RESPONSE = ['n', 'no', 'nah', 'nay', 'f', 'false']
    END_RESPONSE = ['s', 'stop', 'e', 'end', 'exit', 'h', 'halt', 'q', 'quit']
    YTDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist':'True', 'quiet':'True'}
    FILE_PROTOCOL_PREFIX = "file://"
    T = datetime.datetime.now().timestamp()
    
    def create_simple_embed(text="Placeholder Text", type=MessageType.POSITIVE) -> discord.Embed:
        embed = discord.Embed(description=text, color=type.value)
        return embed
        
    # #####################################
    # Debug
    # #####################################

    def print_threads():
        out = f"Threads ({threading.active_count()}): "
        for t in threading.enumerate():
            out = out + f"'{t.name}', "
        print(out)

    def print_time_diff(loc: str):
        global T
        print(f'  {datetime.datetime.now().timestamp() - T}\t:{loc}')
        T = datetime.datetime.now().timestamp()