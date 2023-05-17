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
    BOT_COMMAND_CHANNEL_NAMES = ['bot-spam', 'bot-commands', 'botspam']
    MEDIA_REQUEST_CHANNEL_NAMES = ['jukebox', 'music-requests', 'dj-requests']
    AFFIRMATIVE_RESPONSE = ['y', 'ya', 'ye', 'yea', 'yes', 'yeah', 't', 'true']
    NEGATIVE_RESPONSE = ['n', 'no', 'nah', 'nay', 'f', 'false']
    END_RESPONSE = ['s', 'stop', 'e', 'end', 'exit', 'h', 'halt']
    YTDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist':'True', 'quiet':'True'}
    
    def get_youtube_playable_link(video_url: str) -> str:
        
        import youtube_dl
        youtube = youtube_dl.YoutubeDL(Util.YTDL_OPTIONS)
        try:
            info = youtube.extract_info(video_url, download=False)
            return info['formats'][0]['url']
        except Exception as e:
            print(f"ERROR: something went wrong getting info via YTDL. Will assume input string is the direct media URL: {e}")
            return video_url
    
    def create_simple_embed(text="Placeholder Text", type=MessageType.POSITIVE) -> discord.Embed:
        embed = discord.Embed(description=text, color=type.value)
        return embed
        