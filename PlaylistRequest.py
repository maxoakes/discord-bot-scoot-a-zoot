import discord
import datetime
from MediaSource import MediaSource

class PlaylistRequest:
    __media_source: MediaSource
    __author: discord.Member | discord.User
    __time: datetime.datetime

    def __init__(self, url: str, author: discord.Member | discord.User, is_video=False):
        self.__media_source = MediaSource(url, is_video)
        self.__author = author
        self.__time = datetime.datetime.now()

    def get_request(self):
        return (self.__media_source.get_url(), self.__author, self.__time)
    
    def get_source_string(self):
        return self.__media_source.get_url()
    
    def get_requester(self):
        return self.__author
    
    def update_requester(self, new_author: discord.Member | discord.User):
        self.__author = new_author
        self.__time = datetime.datetime.now()
    
    def is_video(self):
        return self.__media_source.is_video()
    
    def get_request_time(self):
        return self.__time
    
    def __str__(self) -> str:
        return f"`{self.get_source_string()} requested by {self.__author.name}, {self.__time.strftime('%A, %b %d, %I:%M:%S %p.%f %Z')} (is_video:{self.is_video()})`"