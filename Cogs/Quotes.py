import datetime
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
        print(f"Quotes.on_ready(): We have logged in as {Program.bot.user}")


    @commands.command(name="quote", aliases=["q"], hidden=False, 
        brief='Create a quote from a user',
        usage='<add `[quote in quotations] -[author](, time)(, location)`> OR <help>',
        description='Create a quote to add it to the database')
    async def command_quote(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=False):
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
                        print(f"\tAdding to database: with hash {hash} -> {list(map(lambda x: str(x), quote_objects))}")
                        i = 0
                        for quote_object in quote_objects:
                            i = i + 1
                            result = Program.call_procedure_return_scalar("insert_quote_with_set_id", (hash, i, context.guild.id, quote_object.quote, quote_object.author, quote_object.time_place))
                            print(f"\tinsert_quote_with_set_id -> {result} at {datetime.datetime.now()}")

                    await context.reply(f"Your quote has been added to the database.")
                except:
                    await context.reply(f"No positive response recieved. No quote will be added.")

            case "random" | "r" | "get" | "g":
                import random
                async with context.typing():
                    conversation_ids = Program.run_query_return_rows("SELECT DISTINCT set_id FROM discord.quotes WHERE guild_id=(%s)", (context.guild.id,))
                    choices = list(sum(conversation_ids, ()))
                    chosen = random.choice(choices)

                    chosen_quotes: list[Quote] = []

                    quote_set_rows = Program.run_query_return_rows("SELECT quote, author, time_place FROM discord.quotes WHERE set_id=(%s) ORDER BY ordering", (chosen,))
                    for quote_string, quote_author, quote_time_place in quote_set_rows:
                        chosen_quotes.append(Quote(quote_string, quote_author, quote_time_place))

                    message_content = "\n".join(list(map(lambda x: f"> # {x.get_markdown_string()}", chosen_quotes)))
                await context.send(f"Quote of the day:\n{message_content}")
                    
            # unknown command or help
            case _:
                await context.reply("To use this command, utilize the `code` markdown to encompass the quote. Everything inside the single backtick characters will be parsed"
                                    "```!quote add `\"This is a quote\" -Scouter` ```")
                


