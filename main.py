import discord
import os
from dotenv import load_dotenv
from Quote import Quote
from Command import Command

# env and client setup
load_dotenv()
intents = discord.Intents.all()
client = discord.Client(intents=intents)
# static variables
AFFIRMATIVE_RESPONSE = ['y', 'ya', 'ye', 'yea', 'yes', 'yeah']
NEGATIVE_RESPONSE = ['n', 'no', 'nah', 'neah']
COMMAND_CHAR = '>>'
DEFAULT_CHANNEL = None

# on startup
@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    global DEFAULT_CHANNEL
    for guild in client.guilds:
        print(guild)
        DEFAULT_CHANNEL = guild.system_channel # first backup channel
        if DEFAULT_CHANNEL != None:
            print(f"Found a default channel in {DEFAULT_CHANNEL}")
        for channel in guild.channels:
            # print(f"\tChannel: {channel.name}, Type: {channel.type.name}, isDefault: {channel == DEFAULT_CHANNEL}")
            if channel.name.find('bot-') == 0:
                print(f"Found a (likely) bot-specific channel in {channel.name}")
                DEFAULT_CHANNEL = channel # first choice channel
            if DEFAULT_CHANNEL == None:
                print("I have not found a default channel yet!")
                if channel.permissions_for(guild.me).send_messages:
                    DEFAULT_CHANNEL = channel # last resort channel
                    print(f"I have found a default channel at {channel.name}")
    await DEFAULT_CHANNEL.send("I have arrived.")

# user commands
@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return
    
    def check(m): # checking if it's the same user and channel
        return m.author == message.author and m.channel == message.channel
    
    # check if it is a command
    if message.content.startswith(COMMAND_CHAR):
        command = Command(message.content[len(COMMAND_CHAR):].strip())
        # await message.channel.send(command) # verbose

        # route command to different things
        match command.get_part(0):
            # ping-pong to test response
            case 'pong':
                await message.reply('pong')

            # quotes
            case 'quote':
                add_to_db = False
                quote = Quote()
                # match the verb of the command
                match command.get_part(1):
                    case 'add':
                        add_to_db = True
                        quote = Quote(quote=command.get_arg('quote').replace('"', '').replace("'", ''), 
                                    author=command.get_arg('author'), 
                                    location=command.get_arg('location'), 
                                    time=command.get_arg('time'))
                    case 'direct':
                        add_to_db = True
                        quote = Quote(perform_parse=True, raw=command.get_command_from(2))
                    case 'help':
                        await message.reply(f'Available options:\
                                            \n`>>quote direct "<quote text>" -<author name>(, <datetime in any format>(, <location or platform> ))`\
                                            \nExample: `>>quote direct "This is a direct quote to add." -Scouter, 2023`\
                                            \n`>>quote add --quote=<quote text without quotation> --author=<author name> --location=<location or platform> --time=<datetime in any format>`\
                                            \nExample: `>>quote add --quote=This is a verbose quote. --author=Scouter --location=Discord--time=2023 >>quote add --quote=This is a less detailed quote. --author=Scouter --time=2023`')
                    case _:
                        await message.reply(f"Not a valid command. Please consult `>>quote help`")

                # add to the database if the action calls for it
                if add_to_db:
                    if quote.is_bad():
                        await message.reply(f"Submitted quote was malformed. Please consult `>>quote help`")
                        return
                    await message.reply(f"**I will add this quote. Is this correct?** (y/n)\n{quote.get_quote_verbose()}")
                    try:
                        response = await client.wait_for('message', check=check, timeout=20.0)
                        if response.content.lower().strip() not in AFFIRMATIVE_RESPONSE:
                            await message.reply(f"I do not see an approval. Canceling")
                        else:
                            # TODO add the quote to the database
                            await message.reply(f"Added it!")
                    except TimeoutError:
                        await message.reply(f"No response provided. Not adding to database.")
                        return
                    
                # send message to channel if there is a quote that came about this message
                if not quote.is_bad():
                    await message.channel.send(f"> {quote}")
                
client.run(os.getenv('TOKEN'))