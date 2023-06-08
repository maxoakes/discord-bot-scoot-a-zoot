import datetime
import discord

class SimpleEmbed:
    __title: str
    __link: str
    __color: str
    __description: str
    __footer: str
    __image_url: str
    __thumbnail_url: str
    __field_pairs: list[dict]

    def __init__(self, embed: discord.Embed):
        self.__title = str(embed.title) if not isinstance(embed.title, discord.embeds._EmptyEmbed) else ''
        self.__link = str(embed.url) if not isinstance(embed.url, discord.embeds._EmptyEmbed) else ''
        is_valid_color = isinstance(embed.color, discord.Color) or isinstance(embed.color, discord.Colour) or isinstance(embed.color, int)
        self.__color = f'rgb({embed.color.r},{embed.color.g},{embed.color.b})' if is_valid_color else ''
        self.__description = str(embed.description) if not isinstance(embed.description, discord.embeds._EmptyEmbed) else ''
        self.__footer = str(embed.footer.text) if not isinstance(embed.footer.text, discord.embeds._EmptyEmbed) else ''
        self.__image_url = str(embed.image.url) if not isinstance(embed.image.url, discord.embeds._EmptyEmbed) else ''
        self.__thumbnail_url = str(embed.thumbnail.url) if not isinstance(embed.thumbnail.url, discord.embeds._EmptyEmbed) else ''
        self.__field_pairs = []
        for field in embed.fields:
            self.__field_pairs.append({'name': field.name, 'value': field.value})

    def get_dict(self):
        obj = {}
        obj['title'] = self.__title
        obj['link'] = self.__link
        obj['color'] = self.__color
        obj['description'] = self.__description
        obj['footer'] = self.__footer
        obj['image'] = self.__image_url
        obj['thumbnail'] = self.__thumbnail_url
        obj['fields'] = self.__field_pairs
        return obj
    
    def __str__(self):
        import json
        return json.dumps(self.get_dict(), indent=4, ensure_ascii=False)