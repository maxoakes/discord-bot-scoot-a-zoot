from LinearPlaylist import LinearPlaylist
from PlaylistRequest import PlaylistRequest

class Util:
    BOT_COMMAND_CHANNEL_NAMES = ['bot-spam', 'bot-commands', 'botspam']
    MEDIA_REQUEST_CHANNEL_NAMES = ['jukebox', 'music-requests', 'dj-requests']
    AFFIRMATIVE_RESPONSE = ['y', 'ya', 'ye', 'yea', 'yes', 'yeah', 't', 'true']
    NEGATIVE_RESPONSE = ['n', 'no', 'nah', 'nay', 'f', 'false']
    END_RESPONSE = ['s', 'stop', 'e', 'end', 'exit', 'h', 'halt']
    FFMPEG_PATH = r"A:/Programs/ffmpeg/bin/ffmpeg.exe"
    YTDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist':'True', 'quiet':'True'}
    FFMPEG_OPTS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn -filter:a "volume=0.25"', 'executable': FFMPEG_PATH}
    FILE_PROTOCOL_PREFIX = "file://"
    YOUTUBE_URL_PREFIX_FULL = "https://www.youtube.com/watch?"
    YOUTUBE_URL_PREFIX_SHORT = "https://youtu.be/"
    
    def get_youtube_playable_link(video_url: str) -> str:
        import youtube_dl
        if video_url.find(Util.YOUTUBE_URL_PREFIX_FULL) > -1 or video_url.find(Util.YOUTUBE_URL_PREFIX_SHORT) > -1:
            youtube = youtube_dl.YoutubeDL(Util.YTDL_OPTIONS)
            info = youtube.extract_info(video_url, download=False)
            return info['formats'][0]['url']
        else:
            return video_url
        
    def get_file_location_from_url(file_protocol: str) -> str:
        return file_protocol[len(Util.FILE_PROTOCOL_PREFIX):]
        
    def create_playlist_item_embed(request: PlaylistRequest, playlist: LinearPlaylist):
        import discord
        from Metadata import Metadata
        metadata = Metadata(request)

        embed = discord.Embed(
            title=metadata.title,
            url=metadata.url,
            color=request.get_requester().color.value,
            # timestamp=request.get_request_time()
        )
        embed.set_thumbnail(url=metadata.image_url)
        embed.add_field(name="Author", value=metadata.author, inline=False)
        embed.add_field(name="Length", value=metadata.runtime, inline=True)
        embed.add_field(name="Views", value=metadata.views, inline=True)
        embed.add_field(name="Created", value=metadata.created_at, inline=True)
        embed.add_field(name="Remaining media in playlist queue", value=len(playlist.get_next_queue()), inline=False)
        embed.set_footer(text=f"Requested by {request.get_requester()} ({request.get_requester().display_name}) on {request.get_request_time().strftime('%A, %b %d, %I:%M:%S %p')}")
        return embed
    
    def create_playlist_embed(playlist: LinearPlaylist, full=False):
        import discord
        from Metadata import Metadata

        # create embed
        embed = discord.Embed(title="Current Playlist", color=discord.Color.green())

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
        