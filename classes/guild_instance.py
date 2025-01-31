import discord
from state import Program   

class GuildInstance:
    _channel_dict: dict[str, discord.TextChannel]
    guild: discord.Guild

    def __init__(self, guild_id) -> None:
        self.guild = Program.bot.get_guild(guild_id)
        self.queued_media = []
        self._channel_dict = {}
    

    def set_channel_type(self, channel_type: str, channel_id) -> discord.TextChannel:
        new_channel = Program.bot.get_channel(channel_id)
        if new_channel is not None:
            self._channel_dict[channel_type] = new_channel
        else:
            raise Exception(f"No such channel with id {channel_id} for '{channel_type}'")
        return new_channel
    
    
    def get_channel_type(self, id) -> str:
        for channel_type, channel in self._channel_dict.items():
            if channel.id == id:
                return channel_type
            
    def get_channel(self, channel_type):
        return self._channel_dict.get(channel_type, None)


    def as_dict(self):
        return {k: v.id for k, v in self._channel_dict.items()}
    

    def __str__(self) -> str:
        return f"Server='{self.guild}';Channels='{self._channel_dict}';"
    