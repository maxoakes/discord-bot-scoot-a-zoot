from enum import Enum
import discord
from LinearPlaylist import LinearPlaylist
from PlaylistRequest import PlaylistRequest

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
    FILE_PROTOCOL_PREFIX = "file://"
    YOUTUBE_URL_PREFIX_FULL = "https://www.youtube.com/watch?"
    YOUTUBE_URL_PREFIX_SHORT = "https://youtu.be/"
    
    def get_youtube_playable_link(video_url: str) -> str:
        
        import youtube_dl
        youtube = youtube_dl.YoutubeDL(Util.YTDL_OPTIONS)
        try:
            info = youtube.extract_info(video_url, download=False)
            return info['formats'][0]['url']
        except Exception as e:
            print(f"ERROR: something went wrong getting info via YTDL. Will assume input string is the direct media URL: {e}")
            return video_url

        
    def get_file_location_from_url(file_protocol: str) -> str:
        return file_protocol[len(Util.FILE_PROTOCOL_PREFIX):]
        
    def create_playlist_item_embed(request: PlaylistRequest, playlist: LinearPlaylist, type=MessageType.POSITIVE):
        from Metadata import Metadata
        metadata = Metadata(request)

        embed = discord.Embed(
            title=metadata.title,
            url=metadata.url if metadata.url.find('http') > -1 else None,
            color=type.value,
            # timestamp=request.get_request_time()
        )
        embed.set_thumbnail(url=metadata.image_url)
        embed.add_field(name="Source", value=metadata.truncated_url, inline=False)
        embed.add_field(name="Author", value=metadata.author, inline=False)
        embed.add_field(name="Length", value=metadata.runtime, inline=True)
        embed.add_field(name="Views", value=metadata.views, inline=True)
        embed.add_field(name="Created", value=metadata.created_at, inline=True)
        embed.add_field(name="Remaining media in playlist queue", value=len(playlist.get_next_queue()), inline=False)
        embed.set_footer(text=f"Requested by {request.get_requester().display_name} on {request.get_request_time().strftime('%A, %I:%M:%S %p')} (Opus:{request.use_opus()})")
        return embed
    
    def create_playlist_embed(playlist: LinearPlaylist, full=False, type=MessageType.PLAYLIST_ALL):
        from Metadata import Metadata

        # create embed
        embed = discord.Embed(title="Current Playlist", color=type.value)

        # show history
        if full:
            prev_queue = playlist.get_prev_queue()
            prev_string = ""
            for p in prev_queue:
                m = Metadata(p)
                prev_string = prev_string + f"{m.title} by {m.author} ({m.runtime})\n"
            embed.add_field(name="Play History", value=prev_string, inline=False)
        
        # show now playing
        now_playing = playlist.get_now_playing()
        curr = Metadata(now_playing)
        embed.add_field(name="Now Playing", value=f"{curr.title} by {curr.author} ({curr.runtime})", inline=False)

        # show queue
        next_queue = playlist.get_next_queue()
        queue_string = ""
        for i, n in enumerate(next_queue):
            m = Metadata(n)
            queue_string = queue_string + f"{i+1}. {m.title} by {m.author} ({m.runtime})\n"
        embed.add_field(name="Queue", value=queue_string, inline=False)
        return embed
    
    def create_simple_embed(text="Placeholder Text", type=MessageType.POSITIVE) -> discord.Embed:
        embed = discord.Embed(description=text, color=type.value)
        return embed
        