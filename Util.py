import os
import datetime
import threading
import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv
from enum import Enum

class MessageType(Enum):
    FATAL = 0xDC3545 #Red
    NEGATIVE = 0xFFC107 #Orange
    POSITIVE = 0x28A745 #Green
    INFO = 0x17A2B8 #Gray/Blue
    PLAYLIST_ITEM = 0x007BFF #Blue
    PLAYLIST_ALL = 0x007BFF #Blue
    QUOTE = 0x007BFF #Blue

class ResponseType(Enum):
    TEXT = 0,
    JSON = 1,
    XML = 2,
    UNKNOWN = 3

class Util:

    AFFIRMATIVE_RESPONSE = ['y', 'ya', 'ye', 'yea', 'yes', 'yeah', 't', 'true']
    NEGATIVE_RESPONSE = ['n', 'no', 'nah', 'nay', 'f', 'false']
    END_RESPONSE = ['s', 'stop', 'e', 'end', 'exit', 'h', 'halt', 'q', 'quit']
    YTDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist':'True', 'quiet':'True'}
    FILE_PROTOCOL_PREFIX = "file://"
    T = datetime.datetime.now().timestamp()
    
    __env_loaded = False
    __command_char = '>>'
    __author_mention = 'Author Unspecified'
    
    def get_command_char():
        if not Util.__env_loaded:
            load_dotenv()
            Util.__command_char = os.getenv('COMMAND_CHAR')
        return Util.__command_char

    def get_author_mention():
        if not Util.__env_loaded:
            load_dotenv()
            Util.__author_mention = os.getenv('AUTHOR_MENTION')
        return Util.__author_mention

    def create_simple_embed(text="Placeholder Text", type=MessageType.POSITIVE) -> discord.Embed:
        embed = discord.Embed(description=text, color=type.value)
        return embed
        
    async def http_get_thinking(url: str, context: commands.Context) -> tuple[dict | str, ResponseType, int]:
        async with context.channel.typing():
            return await Util.http_get(url)

    async def http_get(url: str) -> tuple[dict | str, ResponseType, int]:
        print(f'GET {url}')
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                content_type: str = response.headers.get('content-type')
                mime = ResponseType.UNKNOWN
                if content_type.find('application/json') > -1:
                    mime = ResponseType.JSON
                if content_type.find('application') > -1 and content_type.find('xml') > -1:
                    mime = ResponseType.XML
                if content_type.find('text/') > -1:
                    mime = ResponseType.TEXT
                code: int = response.status

                if mime == ResponseType.JSON:
                    return (await response.json(), mime, code)
                else:
                    return (response.text, mime, code)

    def build_embed_fields(embed: discord.Embed, name_values: list[tuple[str, object, bool | None]]) -> None:
        for pairing in name_values:
            # if there is no value given for a field, there was likely not one received in the first place, so skip it
            value_nonexistent = pairing[1] == None or pairing[1] == ''

            if not value_nonexistent:
                title = str(pairing[0])
                value = str(pairing[1])
                inline_override = pairing[2] if len(pairing) == 3 else None
                
                # check if the field is narrow enough to avoid making a newline
                inline_available = len(title) < 20 and len(value) < 25
                is_inline = inline_override if inline_override != None else inline_available
                
                # return
                embed.add_field(name=title, value=value, inline=is_inline)


    def deg_to_compass(num: int) -> str:
        val = int((num/22.5)+.5)
        arr = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]
        return arr[(val % 16)]
    
    
    # good or success
    def is_200(code: int) -> bool:
        return code >= 100 and code < 300
    

    def is_400(code: int) -> bool:
        return code >= 400 and code < 500
    
    
    def is_500(code: int) -> bool:
        return code >= 500 and code < 600
    

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