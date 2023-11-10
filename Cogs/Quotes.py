import discord
from discord.ext import commands
from Bot.Quote import Quote
from Command import Command
from Util import MessageType, Util

class Quotes(commands.Cog):

    possible_channel_names: list
    bot: discord.Bot

    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_ready(self):
        print(f"READY! Initialized Tools cog.")


    # #####################################
    # Manual Checks (does not use built-in cog command checks)
    # #####################################

    def is_command_channel(self, context: commands.Context):
        return isinstance(context.channel, discord.channel.DMChannel) or context.channel.id == Util.DEFAULT_COMMAND_CHANNEL[context.guild.id]


    @commands.command(name='quote', aliases=['q'], hidden=False, 
        brief='Create a quote from a user',
        usage='<direct [quote in quotations] -[author](, time)(, location) OR <add --quote=[quote without quotations] (--author=[author]) (--location=[location]) (--time=[time])>',
        description='Create a quote to add it to the database')
    async def command_quote(self, context: commands.Context):
        command = Command(context.message)        
        if not (self.is_command_channel(context) and context.channel.permissions_for(context.author).kick_members): # kicking seems like an appropriate equivalent trust level
            print(f'{command.get_part(0)} failed permission check. Aborting.')
            return

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
                    quote=command.get_arg('quote', default='<No content>').replace('"', '').replace("'", ''), 
                    author=command.get_arg('author', default='Anonymous'), 
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
                    embed=Util.create_simple_embed(f"This is not a valid command. Please consult `{Util.get_command_char()}help quote`", MessageType.NEGATIVE))

        # add to the database if the action calls for it
        if add_to_db:
            if quote.is_bad():
                await command.get_message().channel.send(content=command.get_author().mention, 
                    embed=Util.create_simple_embed(f"Your quote was malformed. Please consult `{Util.get_command_char()}help quote`", MessageType.FATAL))
                return
            
            # confirm the quote to add, and wait for reply
            await command.get_message().channel.send(f"**{command.get_author().mention}, Is this correct?** (y/n)", embed=quote.get_embed())
            try:
                response: discord.Message = await commands.wait_for('message', check=check_channel_response, timeout=Util.CONFIRMATION_TIME)

                # check if there is an affirmative response from the same person
                if response.content.lower().strip() in Util.AFFIRMATIVE_RESPONSE and command.get_author().id == response.author.id:
                    # TODO implement insert query to local DB
                    await command.get_message().channel.send(content=f'{command.get_author().mention}, (Not implemented) this quote has been added to the database:')
                    await Util.write_dev_log(self.bot, f'A quote was added to the database by {quote.get_creator()}.')
                else:
                    await command.get_message().channel.send(content=f'{command.get_author().mention}, no affirmative response was provided. This quote will **not** be added to the database:')

            except TimeoutError:
                await command.get_message().channel.send(content=f'{command.get_author().mention}, no response was provided. This quote will **not** be added to the database:')
                return
            
        # send message to channel if there is a quote that came about this message
        if not quote.is_bad():
            await command.get_message().channel.send(f"> {quote}")