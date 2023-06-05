import asyncio
import discord
import datetime
from discord.ext import commands

from Util import Util

class Global(commands.Cog):
    bot: discord.Bot

    def __init__(self, bot, channel_names):
        self.bot = bot
        self.possible_channel_names = channel_names
        self._last_member = None


    # on startup
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"We have logged in as {self.bot.user}")

        for guild in self.bot.guilds:
            await self.append_new_server(guild)


    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        if guild is not None:
            await self.append_new_server(guild)


    async def append_new_server(self, guild: discord.Guild):
        temp_default_channel = guild.system_channel

        # attempt to find default command channel
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                if channel.name in self.possible_channel_names:
                    temp_default_channel = channel
                    break
        
        # assign to a fallback channel if bot channel not found
        if temp_default_channel == None:
            print(f"No bot command channel found for {guild.name}, finding default")
            temp_default_channel = guild.system_channel
            if temp_default_channel and temp_default_channel.permissions_for(guild.me).send_messages:
                temp_default_channel = channel

        if temp_default_channel == None:
            print('WARNING, no default command channel is accessible. This bot will not have full functionality.')

        # assign command channel with the server
        Util.DEFAULT_COMMAND_CHANNEL[guild.id] = temp_default_channel.id
        await Util.write_dev_log(self.bot, f'{self.bot.user} initialized for {guild.name}/{temp_default_channel}.')


    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member | discord.User):
        channel = member.guild.system_channel
        if channel is not None:
            await channel.send(f'Welcome {member.mention}.')
            await Util.write_dev_log(self.bot, f'{member} joined server {channel.guild}.')


    @commands.command(name='ping', hidden=True, brief='Get a response')
    async def command_ping(self, context: commands.Context):
        await context.reply(f'pong\n```{datetime.datetime.now().timestamp() - context.message.created_at.timestamp()} ms```')


    @commands.command(name='work', hidden=True)
    async def command_work(self, context: commands.Context, arg=200):
        await Util.write_dev_log(self.bot, f'Work function started on {context.guild}.')
        await context.channel.send(f"Working...")
        q = 2
        for i in range(int(arg)):
            q = pow(q, q) % 500000
            await asyncio.sleep(0.1)
            print((i))
        await context.channel.send(f"Done working {i}")
