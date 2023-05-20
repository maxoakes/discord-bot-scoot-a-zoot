import asyncio
import youtube_dl
import discord
import datetime
from Media.Metadata import Metadata
from Util import MessageType, Util

class PlaylistRequest:
    __raw_source: str
    __author: discord.Member | discord.User
    __time: datetime.datetime
    __use_opus: bool
    __metadata: Metadata

    def __init__(self, url: str, author: discord.Member | discord.User, opus: bool):
        self.__raw_source = url
        self.__author = author
        self.__use_opus = opus
        self.__time = datetime.datetime.now()
        self.__metadata = None

    async def create_metadata(self, is_file=False):
        t = datetime.datetime.now()
        youtube = youtube_dl.YoutubeDL(Util.YTDL_OPTIONS)
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, lambda: youtube.extract_info(self.__raw_source, download=False))
        self.__metadata = Metadata(self.__raw_source, info, is_file)
        print(f"metadata build time: {datetime.datetime.now().timestamp() - t.timestamp()}")
        return self.__metadata
    
    def get_metadata(self):
        if not self.__metadata:
            print(f"Had to force-acquire metadata for request: {self.__raw_source}")
            self.create_metadata()
        return self.__metadata
    
    def get_playable_url(self):
        return self.get_metadata().playable_url
    
    def get_source_string(self):
        return self.__raw_source
    
    def get_requester(self):
        return self.__author
    
    def update_requester(self, new_author: discord.Member | discord.User):
        self.__author = new_author
        self.__time = datetime.datetime.now()
    
    def get_request_time(self):
        return self.__time
    
    def use_opus(self):
        return self.__use_opus
    
    def get_embed(self, type=MessageType.POSITIVE, pos=0):
        metadata = self.__metadata

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
        if pos > 0:
            embed.add_field(name="Position in queue", value=pos, inline=False)
        embed.set_footer(text=f"Requested by {self.get_requester().display_name} on {self.get_request_time().strftime('%A, %I:%M:%S %p')} (Opus:{self.use_opus()})")
        return embed
    
    def __str__(self) -> str:
        return f"`{self.__raw_source} requested by {self.__author.name}, {self.__time.strftime('%A, %b %d, %I:%M:%S.%f %p %Z')})`"