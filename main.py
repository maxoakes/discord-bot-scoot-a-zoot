import os
import sys
import discord
from discord.ext import commands
from dotenv import load_dotenv
from Cogs.Events import Events
from Cogs.Global import Global
from Util import Util
from Cogs.Media import Media
from Cogs.Tools import Tools

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=Util.get_command_char(), intents=intents)

# parse input
input_string = ''
if len(sys.argv) > 1:
    input_string = sys.argv[1]
else:
    input_string = input('What mode to start? [media|bot]: ').strip().lower()

# load token string
load_dotenv()
token = None
if os.getenv('IS_DEV') in Util.AFFIRMATIVE_RESPONSE:
    token = os.getenv('DEV_TOKEN')

# run the appropriate bot
command_channels = []
if input_string in ['media', 'dj', 'player']:
    token = os.getenv('DJ_TOKEN') if not token else token
    command_channels = ['jukebox', 'music-requests', 'dj-requests']
    bot.add_cog(Global(bot, command_channels))
    bot.add_cog(Media(bot))

elif input_string in ['bot', 'chat', 'net', 'text']:
    token = os.getenv('BOT_TOKEN') if not token else token
    command_channels = ['bot-spam', 'bot-commands', 'botspam']
    bot.add_cog(Tools(bot))
    bot.add_cog(Events(bot))
    bot.add_cog(Global(bot, command_channels))

if token:
    bot.run(token)
else:
    print('No valid input was given. Exiting.')
