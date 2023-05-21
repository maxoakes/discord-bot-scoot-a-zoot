import datetime
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from Bot.Call import Call
from Bot.Quote import Quote
from Command import Command
from Util import MessageType, Util

CONFIRMATION_TIME = 20.0
load_dotenv()
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=Command.COMMAND_CHAR, intents=intents)
default_channels: dict[int, int] = {} # [key=guild id, val=channel id]

# on startup
@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")

    global default_channels
    for guild in bot.guilds:
        temp_default_channel = guild.system_channel

        # attempt to find default command channel
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                if channel.name in ['bot-spam', 'bot-commands', 'botspam']:
                    temp_default_channel = channel
        
        # assign to a fallback channel if bot channel not found
        if temp_default_channel == None:
            print(f"No bot command channel found for {guild.name}, finding default")
            temp_default_channel = guild.system_channel
            if temp_default_channel and temp_default_channel.permissions_for(guild.me).send_messages:
                temp_default_channel = channel

        if temp_default_channel == None:
            print('WARNING, no default command channel is accessible. This bot will not have full functionality.')

        # assign command channel with the server
        default_channels[guild.id] = temp_default_channel.id
        print(f"Initialized for '{guild.name}' with channel={temp_default_channel}")
    print("READY!")


# #####################################
# Commands
# #####################################

@bot.command(name='ping', aliases=['pp'], hidden=True, brief='Get a response')
async def command_ping(context: commands.Context):
    await context.reply(f'pong\n```{datetime.datetime.now().timestamp() - context.message.created_at.timestamp()} ms```')


@bot.command(name='quote', aliases=['q'], hidden=False, brief='Create or get a quote from a user')
async def command_quote(context: commands.Context):
    command = Command(context.message)

    def check_channel_response(m): # checking if it's the same user and channel
        return m.author == command.get_author() and m.channel == command.get_channel()
    
    add_to_db = False
    quote: Quote
    # match the verb of the command
    match command.get_part(1):
        # create a quote carefully using flags
        case 'add' | 'a':
            add_to_db = True
            quote = Quote(command.get_author().name,
                quote=command.get_arg('quote').replace('"', '').replace("'", ''), 
                author=command.get_arg('author'), 
                location=command.get_arg('location'), 
                time=command.get_arg('time'))
            
        # create a quote like one would do if they were writing text
        case 'direct' | 'd':
            add_to_db = True
            quote = Quote(command.get_author().name, perform_parse=True, raw=command.get_command_from(2))

        # get a quote from a database
        case 'get' | 'g':
            # TODO implement SQL select query to local DB
            pass

        # unknown command
        case _:
            await command.get_message().channel.send(content=command.get_author().mention, 
                embed=Util.create_simple_embed(f"This is not a valid command. Please consult `{Command.COMMAND_CHAR}help quote`", MessageType.NEGATIVE))

    # add to the database if the action calls for it
    if add_to_db:
        if quote.is_bad():
            await command.get_message().channel.send(content=command.get_author().mention, 
                embed=Util.create_simple_embed(f"Your quote was malformed. Please consult `{Command.COMMAND_CHAR}help quote`", MessageType.FATAL))
            return
        
        # confirm the quote to add, and wait for reply
        await command.get_message().channel.send(f"**{command.get_author().mention}, I will add this quote. Is this correct?** (y/n)", embed=quote.get_embed())
        try:
            response: discord.Message = await bot.wait_for('message', check=check_channel_response, timeout=CONFIRMATION_TIME)

            # check if there is an affirmative response from the same person
            if response.content.lower().strip() in Util.AFFIRMATIVE_RESPONSE and command.get_author().id == response.author.id:
                # TODO implement insert query to local DB
                await command.get_message().channel.send(content=f'{command.get_author().mention}, this quote will **not** be added to the database:')
            else:
                await command.get_message().channel.send(content=f'{command.get_author().mention}, no affirmative was provided. This quote will **not** be added to the database:')

        except TimeoutError:
            await command.get_message().channel.send(content=f'{command.get_author().mention}, no response was provided. This quote will **not** be added to the database:')
            return
        
    # send message to channel if there is a quote that came about this message
    if not quote.is_bad():
        await command.get_message().channel.send(f"> {quote}")


@bot.command(name='minecraft', aliases=['mc'], hidden=False, brief='Get the status of a Minecraft server')
async def command_minecraft(context: commands.Context):
    command = Command(context.message) 
    response = Call.minecraft_server(command.get_command_from(1))
    await command.get_channel().send(response)


bot.run(os.getenv('BOT_TOKEN'))