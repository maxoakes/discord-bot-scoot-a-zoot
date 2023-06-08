import datetime

import discord

from Bot.SimpleMessage import SimpleMessage

class MessageDump:
    __start_time: datetime
    __end_time: datetime
    __guild: str
    __channel: str
    __messages: list[SimpleMessage]

    def __init__(self, start_time, end_time, guild: discord.Guild, channel, messages: list[discord.Message]):
        self.__start_time = start_time
        self.__end_time = end_time
        self.__guild = guild.name
        self.__channel = channel.name
        self.__messages = []
        for message in messages:
            self.__messages.append(SimpleMessage(message))

    def get_dict(self):
        obj = {}
        obj['start_time'] = datetime.datetime.isoformat(self.__start_time)
        obj['end_time'] = datetime.datetime.isoformat(self.__end_time)
        obj['guild'] = self.__guild
        obj['channel'] = self.__channel
        message_output = []
        for message in self.__messages:
            message_output.append(message.get_dict())
        obj['messages'] = message_output
        return obj
    
    def __str__(self):
        import json
        return json.dumps(self.get_dict(), indent=4, ensure_ascii=False)