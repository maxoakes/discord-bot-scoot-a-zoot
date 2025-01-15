import json
import os
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


    def get_command_channel(self) -> discord.TextChannel:
        return self._channel_dict.get("command")
    

    def get_channel(self, type: str) -> discord.TextChannel:
        channel = self._channel_dict.get(type)
        if (channel is None):
            return self._channel_dict.get("command")
        else:
            return channel
    
    
    def get_channels(self) -> dict[str, discord.TextChannel]:
        return self._channel_dict
    
    
    def get_channel_type(self, id) -> str:
        for channel_type, channel in self._channel_dict.items():
            if channel.id == id:
                return channel_type


    def write_settings_file(self) -> bool:
        filepath = fr"{Program.GUILD_SETTINGS_DIRECTORY_PATH}/{self.guild.id}.json"
        package = {"guild_id": self.guild.id} | dict(map(lambda item: (item[0], item[1].id), self._channel_dict.items()))
        with open(filepath, "w") as file:
            json.dump(package, file, indent=4)
        print(f"Guild settings file written for {self.guild}")
        return True


    def load_settings_file(self):
        guild_filename = fr"{Program.GUILD_SETTINGS_DIRECTORY_PATH}/{self.guild.id}.json"
        if os.path.exists(guild_filename):
            with open(guild_filename) as json_file:
                settings = json.load(json_file)
                self.load_channels_dict(settings)


    def load_channels_dict(self, data: dict[str, int]) -> bool:
        for channel_type, channel_id in data.items():
            if channel_type == "guild_id":
                print(f"Loading settings for {channel_type}:{channel_id}")
            else:
                channel = Program.bot.get_channel(channel_id)
                self._channel_dict[channel_type] = channel
    

    def __str__(self) -> str:
        return f"Server='{self.guild}';Channels='{self._channel_dict}';"
    