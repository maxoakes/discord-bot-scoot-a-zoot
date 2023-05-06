import discord
from Command import Command
from PlaylistRequest import PlaylistRequest

class Playlist:
    __client_ref: discord.Client
    __play_id: int
    __manual_movement: bool

    __now_playing: PlaylistRequest
    __next_list: list[PlaylistRequest] # queue
    __prev_list: list[PlaylistRequest] # stack
    # [prev_list] + now_playing + [next_list]
    
    def __init__(self, client: discord.Client):
        self.__play_id = 0
        self.__next_list = []
        self.__prev_list = []
        self.__now_playing = None
        self.__manual_movement = False
        self.__client_ref = client

    def set_manual(self, is_manual):
        self.__manual_movement = is_manual

    def is_manual(self):
        return self.__manual_movement

    def add_queue(self, request: PlaylistRequest):
        self.__next_list.append(request)
        self.__client_ref.dispatch("media_playlist_update")
        return self.__next_list
    
    def get_next_queue(self):
        if len(self.__next_list) > 0:
            return self.__next_list[0]
        else:
            return None
    
    def iterate_queue(self):
        if len(self.__next_list) > 0:
            # if there is something playing, move it to the previously played list
            if self.__now_playing:
                self.__prev_list.append(self.__next_list[0])

            # set the new currently playing media
            self.__now_playing = self.__next_list[0]
            self.__play_id = self.__play_id + 1

            # update queue
            self.__next_list = self.__next_list[1:]
            self.__client_ref.dispatch("media_playlist_update")
        else:
            self.__now_playing = None
        self.__manual_movement = False
        return self.__now_playing
        
    def move_back_queue(self):
        if len(self.__prev_list) > 0:
            # push the queue back
            self.__next_list = [self.__now_playing] + self.__next_list
            self.__now_playing = self.__prev_list[-1]
            self.__play_id = self.__play_id + 1
            self.__prev_list = self.__prev_list[:-1]
            self.__client_ref.dispatch("media_playlist_update")
            self.__manual_movement = False
        return self.__now_playing
        
    def clear_queue(self, clear_prev=False):
        self.__next_list = []
        if clear_prev:
            self.__prev_list = []
        self.__client_ref.dispatch("media_playlist_update")
        return
    
    def get_now_playing(self):
        return self.__now_playing
    
    def get_full_queue(self):
        return self.__next_list
    
    def get_full_prev_played(self):
        return self.__prev_list
    
    def get_current_play_id(self):
        return self.__play_id
    
    def __str__(self):
        output = ""
        for i in self.__prev_list:
            output = output + f"\n{i}"
        output = output + f"\nNow playing: {self.__now_playing}"
        for i in self.__next_list:
            output = output + f"\n{i}"
        return f"{output}"