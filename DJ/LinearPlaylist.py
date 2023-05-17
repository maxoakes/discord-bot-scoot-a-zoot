import discord
from enum import Enum
from DJ.PlaylistRequest import PlaylistRequest
from Util import MessageType

class PlaylistAction(Enum):
    STAY = 0
    FORWARD = 1
    BACKWARD = 2
    STOP = 3

class LinearPlaylist:
    __client_ref: discord.Client
    __requested_action: PlaylistAction
    __do_progress: bool

    __playlist: list[PlaylistRequest] = []
    __current_index: int = 0 # if -1, the playlist is not initialized
    
    def __init__(self, client: discord.Client):
        self.__playlist = []
        self.__current_index = 0
    
        self.__requested_action = PlaylistAction.STAY
        self.__do_progress = False
        self.__client_ref = client

    # helper
    def is_init(self) -> bool:
        return len(self.__playlist) > 0
    
    def is_end(self) -> bool:
        return len(self.__playlist) == self.__current_index
    
    def request_movement(self, action: PlaylistAction) -> None:
        self.__requested_action = action

    def get_requested_action(self) -> PlaylistAction:
        return self.__requested_action
    
    def allow_progress(self, p: bool) -> None:
        self.__do_progress = p

    def can_progress(self) -> bool:
        return self.__do_progress
    
    def add_queue(self, request: PlaylistRequest) -> list[PlaylistRequest]:
        # initialize the playlist with the first request
        self.__playlist.append(request)
        self.__client_ref.dispatch("media_playlist_update")
        return self.__playlist[self.__current_index:]
    
    def get_next_queue(self) -> list[PlaylistRequest]:
        if not self.is_init() or self.is_end():
            return []
        else:
            return self.__playlist[self.__current_index + 1:]
    
    def get_prev_queue(self) -> list[PlaylistRequest]:
        if not self.is_init():
            return []
        else:
            return self.__playlist[:self.__current_index]
        
    def get_full_playlist(self):
        return (self.__playlist, self.__current_index)
            
    def iterate_queue(self) -> PlaylistRequest:
        if not self.is_init() or self.is_end():
            return None
        else:
            self.__current_index = self.__current_index + 1
            self.__client_ref.dispatch("media_playlist_update")
            if self.is_end():
                return None
            else:
                return self.__playlist[self.__current_index]
        
    def move_back_queue(self) -> PlaylistRequest:
        if not self.is_init():
            return None
        else:
            if self.__current_index == 0:
                return self.__playlist[0]
            else:
                self.__current_index = self.__current_index - 1
                self.__client_ref.dispatch("media_playlist_update")
                return self.__playlist[self.__current_index]
        
    def clear_queue(self, clear_prev=False) -> None:
        if not self.is_init():
            return
        else:
            if clear_prev:
                self.__playlist = [self.__playlist[self.__current_index]]
                self.__current_index = 0
            else:
                self.__playlist = self.__playlist[0:self.__current_index]
            self.__client_ref.dispatch("media_playlist_update")
            return
    
    def get_now_playing(self) -> PlaylistRequest:
        if not self.is_init() or self.is_end():
            return None
        else:
            return self.__playlist[self.__current_index]
    
    def get_embed(self, full=False, type=MessageType.PLAYLIST_ALL):
        from DJ.Metadata import Metadata

        # create embed
        embed = discord.Embed(title="Current Playlist", color=type.value)

        # show history
        if full:
            prev_queue = self.get_prev_queue()
            prev_string = ""
            for p in prev_queue:
                m = Metadata(p)
                prev_string = prev_string + f"{m.title} by {m.author} ({m.runtime})\n"
            embed.add_field(name="Play History", value=prev_string, inline=False)
        
        # show now playing
        now_playing = self.get_now_playing()
        curr = Metadata(now_playing)
        embed.add_field(name="Now Playing", value=f"{curr.title} by {curr.author} ({curr.runtime})", inline=False)

        # show queue
        next_queue = self.get_next_queue()
        queue_string = ""
        for i, n in enumerate(next_queue):
            m = Metadata(n)
            queue_string = queue_string + f"{i+1}. {m.title} by {m.author} ({m.runtime})\n"
        embed.add_field(name="Queue", value=queue_string, inline=False)
        return embed

    def __str__(self):
        if len(self.__playlist) == 0:
            return "There is nothing on the playlist."
        else:
            output = ""
            for i in range(len(self.__playlist)):
                if self.__current_index > i:
                    output = output + f"\n* `{self.__playlist[i]}`"
                elif self.__current_index == i:
                    output = output + f"\nNOW: `{self.__playlist[i]}`"
                else:
                    output = output + f"\n{i-self.__current_index}. `{self.__playlist[i]}`"
            return output