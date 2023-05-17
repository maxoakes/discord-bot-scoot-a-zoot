import os
import sys
import discord
import asyncio
from dotenv import load_dotenv
from Bot.Call import Call
from Help import Help
from Bot.Quote import Quote
from Command import Command
from Util import MessageType, Util

# set up variable storage
load_dotenv()
intents = discord.Intents.all()
client = discord.Client(intents=intents)

# set in on_ready
default_channels: dict[int, int] = {}

# on startup
@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")

    global default_channels
    for guild in client.guilds:
        temp_default_channel = guild.system_channel

        # attempt to find default command channel
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                if channel.name in Util.BOT_COMMAND_CHANNEL_NAMES:
                    temp_default_channel = channel
        
        # if a default command channel is not found, attempt to assign a fallback channel that the users can send commands
        if temp_default_channel == None:
            print(f"\tNo default channel found for {guild.name}, finding default")
            temp_default_channel = guild.system_channel
            if temp_default_channel:
                if temp_default_channel.permissions_for(guild.me).send_messages:
                    temp_default_channel = channel
        if temp_default_channel == None:
            print('WARNING, no default command channel is accessible. This bot will not have full functionality.')

        # send opening message
        await temp_default_channel.send("**I have arrived.**")
        print(f"Initialized for '{guild.name}' with command channel='{temp_default_channel}'")

        # assign command channel with the server
        default_channels[guild.id] = temp_default_channel.id

# user commands
@client.event
async def on_message(message: discord.Message):
    # ignore the bots own messages
    if message.author == client.user:
        return

    # if the message is a command, and in a command channel, try to route and parse it
    if not message.content.startswith(Command.COMMAND_CHAR):
        return
    
    if message.channel.id != default_channels[message.channel.guild.id]:
        return
    
    command = Command(message)
    match command.get_part(0):
        # create or get a quote
        case 'quote':
            await parse_quote_request(command)

        case 'minecraft':
            response = Call.minecraft_server(command.get_command_from(1))
            await command.get_channel().send(response)

        # print the list of commands
        case 'help':
            await command.get_channel().send(Help.get_text_help_markdown(command.get_command_from(1)))

        # there is an unknown command that a user entered in the media text channel
        case _:
            await command.get_channel().send(embed=Util.create_simple_embed(f"Unknown action `{command.get_part(0)}`.", MessageType.NEGATIVE))

# manage commands for adding or displaying quotes
async def parse_quote_request(command: Command):

    def check_channel_response(m): # checking if it's the same user and channel
        return m.author == command.get_author() and m.channel == command.get_channel()
    
    add_to_db = False
    quote: Quote
    # match the verb of the command
    match command.get_part(1):
        # create a quote carefully using flags
        case 'add':
            add_to_db = True
            quote = Quote(command.get_author().name,
                quote=command.get_arg('quote').replace('"', '').replace("'", ''), 
                author=command.get_arg('author'), 
                location=command.get_arg('location'), 
                time=command.get_arg('time'))
            
        # create a quote like one would do if they were writing text
        case 'direct':
            add_to_db = True
            quote = Quote(command.get_author().name, perform_parse=True, raw=command.get_command_from(2))

        # get a quote from a database
        case 'get':
            # TODO implement SQL select query to local DB
            pass

        # unknown command
        case _:
            await command.get_message().channel.send(f"{command.get_author().mention}, this is not a valid command. Please consult `>>help quote`")

    # add to the database if the action calls for it
    if add_to_db:
        if quote.is_bad():
            await command.get_message().channel.send(f"{command.get_author().mention}, your submitted quote was malformed. Please consult `>>help quote`")
            return
        
        # confirm the quote to add, and wait for reply
        await command.get_message().channel.send(f"**{command.get_author().mention}, I will add this quote. Is this correct?** (y/n)", embed=quote.get_embed())
        try:
            response = await client.wait_for('message', check=check_channel_response, timeout=20.0)
            # check if there is an affirmative response from the same person
            if response.content.lower().strip() in Util.AFFIRMATIVE_RESPONSE and command.get_author().id == response.author.id:
                # TODO implement insert query to local DB
                await command.get_message().channel.send(f"{command.get_author().mention}, it has been added to the database.")
            else:
                await command.get_message().channel.send(f"{command.get_author().mention}, no affirmative response was given. Canceling...")
        except TimeoutError:
            await command.get_message().channel.send(f"{command.get_author().mention}, no response was given. Canceling...")
            return
        
    # send message to channel if there is a quote that came about this message
    if not quote.is_bad():
        await command.get_message().channel.send(f"> {quote}")

client.run(os.getenv('BOT_TOKEN'))