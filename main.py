import discord
import os
from dotenv import load_dotenv
from Quote import Quote
from Command import Command

# env and client setup
load_dotenv()
intents = discord.Intents.all()
client = discord.Client(intents=intents)
user_command_char = '>>'
default_channel = None

# on startup
@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    global default_channel
    for guild in client.guilds:
        print(guild)
        default_channel = guild.system_channel # first backup channel
        if default_channel != None:
            print(f"Found a default channel in {default_channel}")
        for channel in guild.channels:
            # print(f"\tChannel: {channel.name}, Type: {channel.type.name}, isDefault: {channel == default_channel}")
            if channel.name.find('bot-') == 0:
                print(f"Found a (likely) bot-specific channel in {channel.name}")
                default_channel = channel # first choice channel
            if default_channel == None:
                print("I have not found a default channel yet!")
                if channel.permissions_for(guild.me).send_messages:
                    default_channel = channel # last resort channel
                    print(f"I have found a default channel at {channel.name}")
    await default_channel.send("I have arrived.")

# user commands
@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return
    
    # check if it is a command
    if message.content.startswith(user_command_char):
        command = Command(message.content[len(user_command_char):].strip())
        # await message.reply(command) # verbose

        # route command to different things
        # ping-pong to test response
        if (command.get_base_command() == 'ping'):
            await message.reply('pong')

        # quotes
        if (command.get_base_command() == 'quote'):
            if (command.get_primary_value() == 'add'):
                quote = Quote(command.get_arg('quote'), command.get_arg('author'), command.get_arg('location'), command.get_arg('time'))
                await message.reply(f"I will add this quote. Is this correct?: {quote}")

                def check(m): # checking if it's the same user and channel
                    return m.author == message.author and m.channel == message.channel

                try:
                    response = await client.wait_for('message', check=check, timeout=20.0)
                    if response.content.lower() not in ['yes', 'y' 'ya', 'yea', 'yeah']:
                        await message.reply(f"I do not see an approval. Canceling")
                    else:
                        # TODO add the quote to the database
                        await message.reply(f"Added it!")
                        await message.channel.send(f"> {quote.get_quote_short()}")
                except TimeoutError:
                    await message.reply(f"No response provided. Not adding to database.")


            
client.run(os.getenv('TOKEN'))
# https://discord.com/oauth2/authorize?client_id=1102715365299064933&permissions=328635906624&scope=bot