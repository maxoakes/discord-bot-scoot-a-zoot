from enum import Enum
import discord

class MessageType(Enum):
    FATAL = 0xDC3545 #Red
    NEGATIVE = 0xFFC107 #Orange
    POSITIVE = 0x28A745 #Green
    INFO = 0x17A2B8 #Gray/Blue
    PLAYLIST_ITEM = 0x007BFF #Blue
    PLAYLIST_ALL = 0x007BFF #Blue

class Util:
    AFFIRMATIVE_RESPONSE = ['y', 'ya', 'ye', 'yea', 'yes', 'yeah', 't', 'true']
    NEGATIVE_RESPONSE = ['n', 'no', 'nah', 'nay', 'f', 'false']
    END_RESPONSE = ['s', 'stop', 'e', 'end', 'exit', 'h', 'halt', 'q', 'quit']
    YTDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist':'True', 'quiet':'True'}
    
    def create_simple_embed(text="Placeholder Text", type=MessageType.POSITIVE) -> discord.Embed:
        embed = discord.Embed(description=text, color=type.value)
        return embed
        