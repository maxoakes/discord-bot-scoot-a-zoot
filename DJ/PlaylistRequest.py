import discord
import datetime

class PlaylistRequest:
    __raw_source: str
    __author: discord.Member | discord.User
    __time: datetime.datetime
    __use_opus: bool

    def __init__(self, url: str, author: discord.Member | discord.User, opus: bool):
        self.__raw_source = url
        self.__author = author
        self.__use_opus = opus
        self.__time = datetime.datetime.now()

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
    
    def __str__(self) -> str:
        return f"`{self.__raw_source} requested by {self.__author.name}, {self.__time.strftime('%A, %b %d, %I:%M:%S.%f %p %Z')})`"