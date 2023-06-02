import asyncio
import discord
import datetime
from discord.ext import commands

class Global(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None


    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member | discord.User):
        channel = member.guild.system_channel
        if channel is not None:
            await channel.send(f'Welcome {member.mention}.')


    @commands.command(name='ping', hidden=True, brief='Get a response')
    async def command_ping(self, context: commands.Context):
        await context.reply(f'pong\n```{datetime.datetime.now().timestamp() - context.message.created_at.timestamp()} ms```')


    @commands.command(name='work', hidden=True)
    async def command_work(context: commands.Context, arg=200):
        await context.channel.send(f"Working...")
        q = 2
        for i in range(int(arg)):
            q = pow(q, q) % 500000
            await asyncio.sleep(0.1)
            print((i))
        await context.channel.send(f"Done working {i}")
