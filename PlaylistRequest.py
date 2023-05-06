import discord
import datetime

class PlaylistRequest:
    __link: str
    __author: discord.Member | discord.User
    __is_video: bool
    __time: datetime.datetime

    def __init__(self, source, requester, is_video):
        self.__link = source
        self.__author = requester
        if is_video: # None or False
            self.__is_video = True
        else:
            self.__is_video = False
        self.__time = datetime.datetime.now()

    def get_request(self):
        return (self.__link, self.__author, self.__is_video, self.__time)
    
    def get_source_string(self):
        return self.__link
    
    def get_requester(self):
        return self.__author
    
    def is_video(self):
        return self.__is_video
    
    def get_request_time(self):
        return self.__time
    
    def __str__(self) -> str:
        return f"`{self.__link} requested by {self.__author.name}, {self.__time.strftime('%A, %b %d, %I:%M:%S %p %Z')} (is_video:{self.__is_video})`"