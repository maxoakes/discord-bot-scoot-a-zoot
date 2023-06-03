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
        info = None
        is_unknown_source = False
        if not is_file:
            youtube = youtube_dl.YoutubeDL(Util.YTDL_OPTIONS)
            loop = asyncio.get_event_loop()
            try:
                info = await loop.run_in_executor(None, lambda: youtube.extract_info(self.__raw_source, download=False))
            except youtube_dl.utils.DownloadError as e:
                print(f'YTDL error in create_metadata(): {e}')
                is_unknown_source = True
            except Exception as e:
                print (f'Unknown error: {e}')
                is_unknown_source = True

        self.__metadata = Metadata(self.__raw_source, info, is_file, is_unknown_source)
        print(f"Metadata build time for {self.__metadata.title}: {datetime.datetime.now().timestamp() - t.timestamp()}")
        return self.__metadata
    
    async def get_metadata(self):
        if not self.__metadata:
            print(f"Had to force-acquire metadata for request: {self.__raw_source}")
            await self.create_metadata()
        return self.__metadata
    
    async def get_playable_url(self):
        meta = await self.get_metadata()
        return meta.playable_url
    
    def get_source_string(self):
        return self.__raw_source
    
    def get_requester(self):
        return self.__author
    
    def get_guild(self):
        return self.__author.guild
    
    def update_requester(self, new_author: discord.Member | discord.User):
        self.__author = new_author
        self.__time = datetime.datetime.now()
    
    def get_request_time(self):
        return self.__time
    
    def use_opus(self):
        return self.__use_opus
    
    async def get_embed(self, type=MessageType.POSITIVE, pos=0):
        metadata = await self.get_metadata()

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
    

    async def get_playlist_summary(self) -> str:
        meta = await self.get_metadata()
        return f"*{meta.title}* by *{meta.author}* in `{self.get_guild()}` ({meta.runtime})"
    

    def __str__(self) -> str:
        return f"`{self.__raw_source} requested by {self.__author.name}, {self.__time.strftime('%A, %b %d, %I:%M:%S.%f %p %Z')})`"