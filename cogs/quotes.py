import asyncio
import datetime
import math
import discord
from discord.ext import commands
from classes.quote import Quote
from classes.text_command import TextCommand
from state import Program, Utility

class QuoteCog(commands.Cog):

    _default_channel_type: str

    def __init__(self):
        self._default_channel_type = "command"


    @commands.Cog.listener()
    async def on_ready(self):
        Program.log(f"Quotes.on_ready(): We have logged in as {Program.bot.user}",0)
        while True:
            # get seconds to next qotd time
            now = datetime.datetime.now()
            seconds_to_first_message = (datetime.datetime.combine(now + datetime.timedelta(days=1), datetime.time(hour=4)) - now).seconds
            Program.log(f"QotD message will occur in {math.floor(seconds_to_first_message/60)} minutes.",0)
            await asyncio.sleep(seconds_to_first_message)

            # do qotd
            Program.log(f"Sending quote of the day now!",0)
            guild_channel_rows = Program.run_query_return_rows("SELECT guild_id, channel_id FROM discord.qotd_subscription", ())
            for guild_id, channel_id in guild_channel_rows:
                await self.run_qotd(guild_id, channel_id)

            # wait for time to pass
            await asyncio.sleep(120)

    
    async def run_qotd(self, guild_id, channel_id):
        # delete the last quote of the day
        if Program.DO_DELETE_PREVIOUS_QOTD:
            last_message_id_rows = Program.run_query_return_rows("SELECT last_message_id FROM qotd_subscription WHERE guild_id=(%s) AND channel_id=(%s)", (guild_id, channel_id))
            for message_id_row in last_message_id_rows:
                message_id = message_id_row[0]
                if message_id != None:
                    try:
                        channel: discord.TextChannel = Program.bot.get_channel(channel_id)
                        last_message = await channel.fetch_message(message_id)
                        await last_message.delete()
                        Program.log(f"Last message {message_id} was deleted.",0)
                    except discord.errors.NotFound:
                        Program.log(f"Last message {message_id} was not found; ignoring.",0)
                else:
                    Program.log(f"No previous qotd message was found for {guild_id}/{channel_id}.",1)

        channel = Program.bot.get_channel(channel_id)
        message_content = await self.get_random_quote_from_guild(guild_id)
        message = await channel.send(f"Quote of the day:\n{message_content}")
        result = Program.call_procedure_return_scalar("update_qotd_message_id", (guild_id, channel_id, message.id))


    @commands.command(name="quote", aliases=["q"], hidden=False, 
        brief='Create a quote from a user',
        usage='<add `[quote in quotations] -[author](, time)(, location)`> OR <help>',
        description='Create a quote to add it to the database')
    async def command_quote(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=False):
            return
        if not context.author.guild_permissions.manage_messages:
            await context.reply(f"You do not have the required permissions: `manage_messages`.")
            return
        
        command = TextCommand(context)
        match command.get_part(1):
            case 'add' | 'a':
                quote_objects: list[Quote] = []
                input = command.get_command_from(2)
                input = input.replace("```","`") # If the user did the full code block format, change it back to inline code
                markdown_positions = [i for i, char in enumerate(input) if char == "`"]
                if len(markdown_positions) % 2 == 1:
                    context.reply("Not a valid input (odd number of code markdown characters)")
                    return
                
                raw_quotes: list[str] = []
                markdown_pairs = list(zip(markdown_positions[::2], markdown_positions[1::2]))
                for start, end in markdown_pairs:
                    raw_quotes.append(input[start+1:end])

                for quote in raw_quotes:
                    quote_objects.append(Quote.parse_from_raw(quote))

                # confirm the quote to add, and wait for reply
                question_message = await context.reply(f"**Is this correct?** (y/n)", embeds=list(map(lambda x: x.get_embed(), quote_objects)))
                try:
                    def reply_check(message: discord.Message):
                        return message.author == context.author and message.channel == context.channel and message.content.lower().strip() in Program.AFFIRMATIVE_RESPONSE
    
                    await Program.bot.wait_for('message', check=reply_check, timeout=Program.CONFIRMATION_TIME)
                    

                    async with context.typing():
                        hash = context.message.created_at.__hash__() ^ context.guild.__hash__()
                        Program.log(f"Adding quote to database: with hash {hash} -> [{list(map(lambda x: str(x), quote_objects))}]",1)
                        i = 0
                        for quote_object in quote_objects:
                            i = i + 1
                            result = Program.call_procedure_return_scalar("insert_quote_with_set_id", (hash, i, context.guild.id, quote_object.quote, quote_object.author, quote_object.time_place))
                            Program.log(f"Quote insert with result ({result})",0)

                    await context.reply(f"Your quote has been added to the database.")
                except:
                    await context.reply(f"No positive response recieved. No quote will be added.")

            case "random" | "r" | "get" | "g":
                message_content = ""
                async with context.typing():
                    message_content = await self.get_random_quote_from_guild(context.guild.id)
                await context.send(f"Quote of the day:\n{message_content}")
                    
            # unknown command or help
            case _:
                await context.reply("To use this command, utilize the `code` markdown to encompass the quote. Everything inside the single backtick characters will be parsed"
                                    "```!quote add `\"This is a quote\" -Scouter` ```")
                

    @commands.command(name="set_qotd", hidden=False, 
        brief="Set the channel that will receive the quote of the day for the guild", 
        usage=f"(channel_id) ... NOTE: if no channel_id, the current channel will be used")
    async def command_set_qotd(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=False):
            return
        if not context.author.guild_permissions.manage_messages:
            await context.reply(f"You do not have the required permissions: `manage_messages`.")
            return
        
        command = TextCommand(context)
        input_channel_id = context.channel.id
        # show instructions if wrong syntax
        if not Utility.is_null_or_whitespace(command.get_part(1)):
            try:
                input_channel_id = int(command.get_part(1))
            except:
                await context.reply(f"That channel ID ({command.get_part(1)}) is not valid.")
            return
        
        async with context.typing():
            Program.log(f"Subscribing {input_channel_id} to quote of the day for {context.guild.name}",1)
            result = Program.call_procedure_return_scalar("subscribe_to_qotd", (context.guild.id, input_channel_id))

        # final response to user
        await context.reply(f"{Program.bot.get_channel(input_channel_id).mention} will display the quote of the day.")


    @commands.command(name="qotd", hidden=True, brief="Get the QOTD for this channel")
    async def command_qotd(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=False):
            return
        if not context.author.guild_permissions.manage_messages:
            await context.reply(f"You do not have the required permissions: `manage_messages`.")
            return

        guild_channel_rows = Program.run_query_return_rows("SELECT guild_id, channel_id FROM discord.qotd_subscription WHERE guild_id=(%s) AND channel_id=(%s)", (context.guild.id, context.channel.id))
        for guild_id, channel_id in guild_channel_rows:
            await self.run_qotd(guild_id, channel_id)


# #############################
# Helper Functions
# #############################

    async def get_random_quote_from_guild(self, guild_id) -> str:
        import random
        conversation_ids = Program.run_query_return_rows("SELECT DISTINCT set_id FROM discord.quotes WHERE guild_id=(%s)", (guild_id,))
        choices = list(sum(conversation_ids, ()))
        chosen = random.choice(choices)

        chosen_quotes: list[Quote] = []

        quote_set_rows = Program.run_query_return_rows("SELECT quote, author, time_place FROM discord.quotes WHERE set_id=(%s) ORDER BY ordering", (chosen,))
        for quote_string, quote_author, quote_time_place in quote_set_rows:
            chosen_quotes.append(Quote(quote_string, quote_author, quote_time_place))

        return "\n".join(list(map(lambda x: f"> # {x.get_markdown_string()}", chosen_quotes)))