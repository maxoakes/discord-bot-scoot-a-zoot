import aiohttp
import discord
from discord.ext import commands
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


class Program:
    CONFIRMATION_TIME = 20.0 # seconds
    CHANNEL_TYPES = ["command", "jukebox", "rss", "localhost" ]
    AFFIRMATIVE_RESPONSE = ["y", "ya", "ye", "yea", "yes", "yeah", "t", "true", "sure"]
    NEGATIVE_RESPONSE = ["n", "no", "nah", "nay", "f", "false", "nope"]
    END_RESPONSE = ["s", "stop", "e", "end", "exit", "h", "halt", "q", "quit"]
    YTDL_OPTIONS = {"format": "bestaudio/best", "noplaylist":"True", "quiet":"True"}
    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn -filter:a "volume=0.33"'}
    WHITELISTED_PROTOCOLS = ["http", "https", "file", "tcp", "udp", "rtp"]
    FILE_PROTOCOL_PREFIX = "file"
    SETTINGS_DIRECTORY_PATH = "settings"
    GUILD_SETTINGS_DIRECTORY_PATH = f"{SETTINGS_DIRECTORY_PATH}/guilds"
    RSS_FEED_SETTINGS_FILE_NAME = "rss_feeds.json"
    MEDIA_PRESETS_FILE_NAME = "media_presets.json"
    MAX_NEW_RSS_STORIES_PER_CYCLE = 3

    bot: commands.Bot
    guild_instances: dict[int, object]
    command_character: str
    control_channel_id: int


    def initialize(command_char: str, control_channel_id: int) -> None:
        Program.command_character = command_char
        Program.bot = commands.Bot(command_prefix=command_char, intents=discord.Intents.all())
        Program.guild_instances = {}
        Program.control_channel_id = control_channel_id


    def get_help_instructions(command_name) -> str:
        return f"Incorrect command usage. Use `{Program.command_character}help {command_name}` for correct usage."
    

    def get_client_error_user_response(code) -> str:
        return f"No valid response. Perhaps the expression could not be parsed. Check the `{Program.command_character}help` entry for this command. ({code})"
    

    def get_server_error_user_response(code) -> str:
        return f"Something went wrong while getting a response. ({code})"


    def get_http_control_server_response(code, context: commands.Context, url: str, additional_info = None) -> str:
        return_string = f"`{code}` error on {context.guild} requesting `{url}`"
        if not additional_info == None:
            return_string += f" Additional info: `{additional_info}`"
        return return_string


    def get_control_channel():
        return Program.bot.get_channel(Program.control_channel_id)


    async def write_dev_log(text: str, embed: discord.Embed | None = None):
        channel = Program.get_control_channel()
        if channel is None:
            print("Cannot find dev channel. Nothing will be written.")
            return
        await channel.send(content=text, embed=embed)
        print(f"Control channel message: {text}")


class Utility:
    def is_valid_command_context(context: commands.Context | None, channel_type="command", is_global_command=True, is_whisper_command=False) -> bool:
        # if it is a whisper
        if context.guild is None:
            return is_whisper_command
        else:
            if is_global_command:
                return True
            else:
                guild_instance = Program.guild_instances.get(context.guild.id, None)
                if guild_instance is None:
                    raise Exception(f"Unknown guild: {context.guild}")
                if guild_instance.get_channel(channel_type).id == context.channel.id:
                    return True
                else:
                    print(f"Incorrect channel {Program.guild_instances[context.guild.id].get_channel(channel_type)}")
                    return False
        

    def create_simple_embed(text="Placeholder Text", type=MessageType.POSITIVE) -> discord.Embed:
        embed = discord.Embed(description=text, color=type.value)
        return embed
    

    async def http_get_thinking(url: str, context: commands.Context) -> tuple[dict | str, ResponseType, int]:
        async with context.channel.typing():
            return await Utility.http_get(url)


    async def http_get(url: str) -> tuple[dict | str, ResponseType, int]:
        print(f"GET {url}")
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                content_type: str = response.headers.get("content-type")
                mime = ResponseType.UNKNOWN
                if content_type.find("application/json") > -1:
                    mime = ResponseType.JSON
                if content_type.find("application") > -1 and content_type.find("xml") > -1:
                    mime = ResponseType.XML
                if content_type.find("text/") > -1:
                    mime = ResponseType.TEXT
                code: int = response.status

                if mime == ResponseType.JSON:
                    return (await response.json(), mime, code)
                else:
                    return (response.text, mime, code)


    def build_embed_fields(embed: discord.Embed, name_values: list[tuple[str, object, bool | None]]) -> None:
        for pairing in name_values:
            # if there is no value given for a field, there was likely not one received in the first place, so skip it
            value_nonexistent = pairing[1] == None or pairing[1] == ""

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
    

    def is_200(code: int) -> bool:
        return code >= 100 and code < 300
    

    def is_400(code: int) -> bool:
        return code >= 400 and code < 500
    
    
    def is_500(code: int) -> bool:
        return code >= 500 and code < 600
    

    def sanitize_file_name(input_name: str) -> str:
        invalid_chars = "#%&{}/$! \":<>*?/+`|=\\@'"
        output_name = input_name
        for char in invalid_chars:
            output_name = output_name.replace(char, "")
        while output_name.find("-") == 0 or output_name.find(".") == 0 or output_name.find("_") == 0:
            output_name = output_name[1:]
        return output_name
    

    def is_null_or_whitespace(input: str) -> bool:
        return input is None or input.isspace() or len(input) == 0 
