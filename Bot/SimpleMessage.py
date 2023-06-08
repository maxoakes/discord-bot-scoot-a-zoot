import datetime
import discord
from Bot.SimpleEmbed import SimpleEmbed

class SimpleMessage:
    __id: int
    __created_at: datetime
    __last_edited: datetime
    __author: discord.Member | discord.User
    __message_type: str
    __is_pinned: bool
    __content: str
    __reacts: list[str]
    __embeds: list[SimpleEmbed]

    def __init__(self, message: discord.Message):
        self.__id = message.id
        self.__created_at = message.created_at
        self.__last_edited = message.edited_at
        self.__author = message.author
        self.__message_type = message.type.name
        self.__is_pinned = message.pinned
        self.__content = message.content
        self.__reacts = []
        for react in message.reactions:
            self.__reacts.append(react.emoji)
        self.__embeds = []
        for embed in message.embeds:
            self.__embeds.append(SimpleEmbed(embed))

    def get_dict(self):
        obj = {}
        obj['id'] = self.__id
        obj['created_at'] = datetime.datetime.isoformat(self.__created_at) if self.__created_at else ''
        obj['last_edited'] = datetime.datetime.isoformat(self.__last_edited) if self.__last_edited else ''
        obj['author'] = {'display_name': self.__author.display_name, 'user_tag': str(self.__author)}
        obj['type'] = self.__message_type
        obj['pinned'] = self.__is_pinned
        obj['content'] = self.__content
        obj['reacts'] = self.__reacts
        output_embeds = []
        for embed in self.__embeds:
            output_embeds.append(embed.get_dict())
        obj['embeds'] = output_embeds
        return obj
    
    def __str__(self):
        import json
        return json.dumps(self.get_dict(), indent=4, ensure_ascii=False)