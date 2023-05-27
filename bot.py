import asyncio
import datetime
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from Bot.Quote import Quote
from Command import Command
from Util import MessageType, ResponseType, Util

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


@bot.add_check
def check_command_context(context: commands.Context):
    return context.message.channel.id == default_channels[context.guild.id]


# #####################################
# Commands
# #####################################

@bot.command(name='ping', hidden=True, brief='Get a response')
async def command_ping(context: commands.Context):
    await context.reply(f'pong\n```{datetime.datetime.now().timestamp() - context.message.created_at.timestamp()} ms```')


@bot.command(name='quote', aliases=['q'], hidden=False, 
    brief='Create a quote from a user',
    usage='<direct [quote in quotations] -[author](, time)(, location) OR <add --quote=[quote without quotations] (--author=[author]) (--location=[location]) (--time=[time])>',
    description='Create a quote to add it to the database')
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


@bot.command(name='minecraft', aliases=['mc'], hidden=False, 
    brief='Get the status of a Minecraft server', 
    usage='[server address]',
    description='Get the status of a Minecraft server. If the server is online, get all significant information.')
async def command_minecraft(context: commands.Context):
    command = Command(context.message)
    address = command.get_command_from(1)
    param = 'ftb.ckwgaming.com' if address == '' else address
    (response, mime, code) = await Util.http_get_thinking(f'https://api.mcsrvstat.us/2/{param}', context)

    if (print_debug_if_needed(command, response)):
        return
    
    # if the response is a json (likely a 200 response)
    if mime == ResponseType.JSON and code == 200:
        # required elements
        full_address = f"{response.get('ip', '?.?.?.?')}:{response.get('port', '?????')}"
        is_online = response.get('online', False)
        status = 'Online' if is_online else 'Offline'
        server_name = response.get('hostname') if response.get('hostname', False) else 'Minecraft Server'
        embed_color = MessageType.POSITIVE.value if is_online else MessageType.NEGATIVE.value

        # craft the embed
        embed = discord.Embed(title=server_name, color=embed_color)
        embed.add_field(name='Address', value=full_address)
        embed.add_field(name='Status', value=status)

        if is_online:
            players_curr = response.get('players').get('online')
            players_max = response.get('players').get('max')
            embed.add_field(name='Player Count', value=f'{players_curr} of {players_max}')
            
            motd = ""
            for string in response.get('motd').get('clean'):
                motd = motd + string + '\n'
            embed.add_field(name='Message of the Day', value=motd, inline=False)

            embed.add_field(name='Version', value=response.get('version', 'Unknown Version'))
            if response.get('mods'):
                embed.add_field(name='Number of Mods', value=len(response.get('mods').get('names', [])), inline=False)

            
        await command.get_channel().send(embed=embed)

    # if it is a bad response
    else:
        await command.get_channel().send(Util.create_simple_embed(f"Unknown error processing request. Code {code}", MessageType.FATAL))


@bot.command(name='bored', hidden=False, 
    brief='Get a suggestion for something to do', 
    usage='(--type=["education|recreational|social|diy|charity|cooking|relaxation|music|busywork]) (--participants=[number] (--free)',
    description='Get a suggestion for something to do')
async def command_bored(context: commands.Context):
    command = Command(context.message)
    options = ''
    if command.get_arg('type'):
        options = options + f'type={command.get_arg("type")}&'
    if command.get_arg('participants'):
        options = options + f'participants={command.get_arg("type")}&'
    if command.does_arg_exist('free'):
        options = options + f'minprice=0&maxprice=0'

    (response, mime, code) = await Util.http_get_thinking(f'http://www.boredapi.com/api/activity?{options}', context)

    if (print_debug_if_needed(command, response)):
        return
    
    # if the response is a json (likely a 200 response)
    if mime == ResponseType.JSON and code == 200:

        # craft the embed
        embed = discord.Embed(title="Activity", color=MessageType.POSITIVE.value)
        embed.add_field(name='What to do', value=response.get('activity', 'Do something fun'), inline=False)
        embed.add_field(name='Type', value=response.get('type', 'Unknown').capitalize())
        embed.add_field(name='Participants', value=response.get('participants', 'At least one'))
        is_free = "Yes!" if response.get('price', 1) == 0 else "No"
        embed.add_field(name='Is it free?', value=is_free)
        await command.get_channel().send(embed=embed)

    # if it is a bad response
    else:
        await command.get_channel().send(embed=Util.create_simple_embed(f"Unknown error processing request. Code {code}", MessageType.FATAL))


@bot.command(name='word', hidden=False, aliases=['w', 'dict', 'dictionary', 'def', 'define'],
    brief='Get the definition(s) of a word', 
    usage='[word]',
    description='Get the definition(s) of a word')
async def command_word(context: commands.Context):
    command = Command(context.message)
    word = command.get_command_from(1)
    (response, mime, code) = await Util.http_get_thinking(f'https://api.dictionaryapi.dev/api/v2/entries/en/{word}', context)

    if (print_debug_if_needed(command, response)):
        return
    
    # if the response is a json (likely a 200 response)
    if mime == ResponseType.JSON and code == 200:
        for usage in response:
            # get the word
            if not usage.get('word'):
                continue
            this_word = usage.get('word').capitalize()

            # for each meaning, get each definition
            for meaning in usage.get('meanings', []):
                part = meaning.get('partOfSpeech')
                embed = discord.Embed(title=f'{this_word} ({part})', url=usage.get('sourceUrls', [None])[0], color=MessageType.POSITIVE.value)
                embed.add_field(name='Phonetics', value=usage.get('phonetic'), inline=False)
                i = 0
                for i, definition in enumerate(meaning.get('definitions')):
                    name = f'{i+1}. Definition'
                    d = definition.get('definition')
                    e = definition.get('example')
                    value = ''
                    if e:
                        value = value + f'{d}\n - Example: *{e}*\n'
                    else:
                        value = value + f'{d}'
                    embed.add_field(name=name, value=value, inline=False)
                embed.add_field(name='Source', value=usage.get('sourceUrls', ['None available'])[0], inline=False)
                await command.get_channel().send(embed=embed)

    # if it is a bad response
    else:
        await command.get_channel().send(embed=Util.create_simple_embed(f"Unknown error processing request. Is that a word? Code {code}", MessageType.FATAL))


@bot.command(name='color', hidden=False,
    brief='Enter a color for its RGB, HSL, hex values and closest name', 
    usage='(name [name of color]) OR (hex [hexidecimal value]) OR ([rgb] [0..255] [0..255] [0..255]) OR (hsl [0..255] [0..100] [0..100])',
    description='Enter a color for its RGB, HSL, hex values and closest name')
async def command_color(context: commands.Context):
    command = Command(context.message)
    value_type = command.get_part(1)
    query_string = 'https://color.serialif.com/'

    # parse command for color components
    # if it is a color code of ints
    if value_type in ['rgb', 'hsl', 'hsl']:
        values = (command.get_part(2), command.get_part(4), command.get_part(4))
        query_string = query_string + f'{value_type}={values[0]},{values[1]},{values[2]}'
    # if it is a name for a color
    elif value_type in ['name', 'word', 'keyword']:
        query_string = query_string + f'keyword={command.get_command_from(2)}'
    # if it is a hex or hex alpha
    elif value_type in ['hex']:
        query_string = query_string + f'{command.get_part(2).replace("0x", "").replace("#", "")}'
    # if the input params were bad
    else:
        await command.get_channel().send(embed=Util.create_simple_embed(f"Not a valid input. See `>>help color`", MessageType.NEGATIVE))
        return

    # when everything is all good, make the request
    (response, mime, code) = await Util.http_get_thinking(query_string, context)

    if (print_debug_if_needed(command, response)):
        return
    
    # this API does not return 400 when it is a bad request...
    if mime == ResponseType.JSON and response.get('status') == 'success':
        base_keyword = response.get('base').get('keyword').capitalize()
        base_rgb = response.get('base').get('rgb').get('value')
        base_hsl = response.get('base').get('hsl').get('value')
        base_hex = response.get('base').get('hex').get('value')

        base_value = int(f'0x{base_hex[1:]}', 16)
        base_title_available = base_keyword != ''
        base_title = base_keyword if base_title_available else base_rgb
        base_embed = discord.Embed(title=f'Requested: {base_title}', color=base_value)
        if base_title_available:
            base_embed.add_field(name='Closest Name', value=base_keyword, inline=False)
        base_embed.add_field(name='Red, Blue, Green', value=base_rgb, inline=False)
        base_embed.add_field(name='Hue, Saturation, Lightness', value=base_hsl, inline=False)
        base_embed.add_field(name='Hexidecimal', value=base_hex, inline=False)
        await command.get_channel().send(embed=base_embed)

        comp_keyword = response.get('complementary').get('keyword').capitalize()
        comp_rgb = response.get('complementary').get('rgb').get('value')
        comp_hsl = response.get('complementary').get('hsl').get('value')
        comp_hex = response.get('complementary').get('hex').get('value')

        comp_value = int(f'0x{comp_hex[1:]}', 16)
        comp_title_available = comp_keyword != ''
        comp_title = comp_keyword if comp_title_available else comp_rgb
        comp_embed = discord.Embed(title=f'Complementary: {comp_title}', color=comp_value)
        if comp_title_available:
            comp_embed.add_field(name='Closest Name', value=comp_keyword, inline=False)
        comp_embed.add_field(name='Red, Blue, Green', value=comp_rgb, inline=False)
        comp_embed.add_field(name='Hue, Saturation, Lightness', value=comp_hsl, inline=False)
        comp_embed.add_field(name='Hexidecimal', value=comp_hex, inline=False)
        await command.get_channel().send(embed=comp_embed)

    # if it is a bad response
    else:
        await command.get_channel().send(embed=Util.create_simple_embed(f"Unknown error processing request. Code {code}", MessageType.FATAL))


@bot.command(name='buzz', hidden=False,
    brief='Generate a buzzword tech phrase',
    description='Generate a buzzword tech phrase')
async def command_buzz(context: commands.Context):
    command = Command(context.message)
    (response, mime, code) = await Util.http_get_thinking('https://corporatebs-generator.sameerkumar.website/', context)

    if (print_debug_if_needed(command, response)):
        return
    
    # this API does not return 400 when it is a bad request...
    if mime == ResponseType.JSON and code == 200:
        phrase = response.get('phrase')
        await command.get_channel().send(f'I present... **{phrase}**')
    # if it is a bad response
    else:
        await command.get_channel().send(embed=Util.create_simple_embed(f"Unknown error processing request. Code {code}", MessageType.FATAL))


@bot.command(name='fact', hidden=False,
    brief='Generate a random fun-fact',
    usage='(--de)',
    description='Generate a random fun-fact. Also supports results in German.')
async def command_fact(context: commands.Context):
    command = Command(context.message)
    suffix = '?language=de' if command.does_arg_exist('de') else ''
    (response, mime, code) = await Util.http_get_thinking(f'https://uselessfacts.jsph.pl/api/v2/facts/random{suffix}', context)

    if (print_debug_if_needed(command, response)):
        return
    
    # this API does not return 400 when it is a bad request...
    if mime == ResponseType.JSON and code == 200:
        fact = response.get('text')
        await command.get_channel().send(f'**Fun Fact:** {fact}')
    # if it is a bad response
    else:
        await command.get_channel().send(embed=Util.create_simple_embed(f"Unknown error processing request. Code {code}", MessageType.FATAL))


@bot.command(name='joke', hidden=False,
    brief='Get a joke',
    usage='[programming|dark|pun|spooky|christmas] (--nsfw) (--religious) (--political) (--racist) (--sexist) (--explicit) (--search=[string]) (--lang=[en|es|de|fr|cs|pt])',
    description='Get a joke. Use --flags to blacklist types of jokes. Not specifying a category will yield any type of joke.')
async def command_joke(context: commands.Context):
    command = Command(context.message)

    # get the list of request categories
    categories = []
    i = 1
    while command.get_part(i) != '':
        categories.append(command.get_part(i))
        i = i + 1
    if len(categories) == 0:
        categories = ['Any']
    categories_string = ','.join(categories)

    # get all blacklisted categories
    blacklisted = []
    for flag in ['religious', 'political', 'racist', 'sexist', 'explicit']:
        if command.does_arg_exist(flag):
            blacklisted.append(flag)
    blacklist_string = f'blacklistFlags={",".join(blacklisted)}&' if len(blacklisted) > 0 else ''

    # get the language parameter
    lang_string = ''
    if command.get_arg('lang') in ['en', 'es', 'de', 'fr', 'cs', 'pt']:
        lang_string = f'lang={command.get_arg("lang")}&'

    # get any string to search
    search_string = ''
    if command.get_arg('search'):
        lang_string = f'contains={command.get_arg("search")}&'

    query_string = f'https://v2.jokeapi.dev/joke/{categories_string}?{lang_string}{blacklist_string}{search_string}'
    print(query_string)
    (response, mime, code) = await Util.http_get_thinking(query_string, context)

    if (print_debug_if_needed(command, response)):
        return
    
    # this API does not return 400 when it is a bad request...
    if mime == ResponseType.JSON and code == 200:
        preface = 'Here is a joke:\n'
        joke_type = response.get('type')
        if joke_type == 'single':
            joke = response.get('joke')
            await command.get_channel().send(f'{preface}*{joke}*')
        elif joke_type == 'twopart':
            setup = response.get('setup')
            delivery = response.get('delivery')
            await command.get_channel().send(f'{preface}*{setup}\n||{delivery}||*')
        else:
            if response.get('code') == 106: # 106 ?= no joke found
                await command.get_channel().send(embed=Util.create_simple_embed("No joke matching the selected criteria. soz", MessageType.NEGATIVE))
            else:
                await command.get_channel().send(embed=Util.create_simple_embed(f"The joke was too good; it broke the API. code={response.get('code', '???')}", MessageType.FATAL))
                
    # if it is a bad response
    else:
        await command.get_channel().send(embed=Util.create_simple_embed(f"Unknown error processing request. Code {code}", MessageType.FATAL))


@bot.command(name='geo', hidden=False, aliases=['loc', 'location', 'geography'],
    brief='Get geographical information from an input',
    usage='[any location input type]',
    description='Get geographical information from an input')
async def command_geo(context: commands.Context):
    command = Command(context.message)
    input_string = command.get_command_from(1)
    if input_string == '':
        await command.get_channel().send(embed=Util.create_simple_embed(f'Enter any search parameter.', MessageType.NEGATIVE))
        return
    
    (response, mime, code) = await Util.http_get_thinking(f'https://geokeo.com/geocode/v1/search.php?q={input_string}?&api={os.getenv("GEOKEO_TOKEN")}', context)
    
    if (print_debug_if_needed(command, response)):
        return
    
    # this API does not return 400 when it is a bad request...
    if mime == ResponseType.JSON and response.get('status') == 'ok':
        for result in response.get('results'):
            geo_class = result.get('class')
            geo_type = result.get('type')
            address: dict = result.get('address_components')
            coords: dict = result.get('geometry').get('location')
            url = f'https://www.google.com/maps/@{coords.get("lat")},{coords.get("lng")},10.0z'
            embed = discord.Embed(title='Location Information', url=url, color=MessageType.POSITIVE.value)

            if geo_class:
                embed.add_field(name='Class', value=geo_class.capitalize())
            
            if geo_type:
                embed.add_field(name='Type', value=geo_type.capitalize())

            if address:
                address_order = ['name', 'island', 'neighbourhood', 'street', 'subdistrict', 'district', 'city', 'state', 'postcode', 'country']
                for component in address_order:
                    value = address.get(component)
                    if value:
                        is_inline = len(value) < 20
                        embed.add_field(name=component.capitalize(), value=address.get(component), inline=is_inline)

            embed.add_field(name='Coordinates', value=f'{round(float(coords.get("lat")), 4)}, {round(float(coords.get("lng")), 4)}', inline=False)
        await command.get_channel().send(embed=embed)

    elif response.get('status') == 'ZERO_RESULTS':
        await command.get_channel().send(embed=Util.create_simple_embed(f'No results. Try describing the location differently.', MessageType.NEGATIVE))

    # if it is a bad response
    else:
        await command.get_channel().send(embed=Util.create_simple_embed(f'Unknown error processing request. Status code {code}', MessageType.FATAL))


@bot.command(name='ip', hidden=False,
    brief='Get (possibly) correct location statistics from an IPv4 address',
    usage='[IPv4 address]',
    description='Get (possibly) correct location statistics from an IPv4 address')
async def command_ip(context: commands.Context):
    command = Command(context.message)
    ip = command.get_command_from(1)
    if ip == '':
         await command.get_channel().send(embed=Util.create_simple_embed(f'Enter an IPv4 address as a parameter.', MessageType.NEGATIVE))
         return
    
    (response, mime, code) = await Util.http_get_thinking(f'https://api.techniknews.net/ipgeo/{ip}', context)
    
    if (print_debug_if_needed(command, response)):
        return
    
    # this API does not return 400 when it is a bad request...
    if mime == ResponseType.JSON and response.get('status') == 'success':
        confirmed_ip = response.get('ip')
        country = response.get('country')
        region = response.get('regionName')
        city = response.get('city')
        zip = response.get('zip')
        latt = response.get('lat')
        long = response.get('lon')
        timezone = response.get('timezone')
        isp = response.get('isp')
        org = response.get('org')
        a_system = response.get('as')
        is_proxy = response.get('proxy')
        is_mobile = response.get('mobile')
        is_cached = response.get('cached')

        url = f'https://www.google.com/maps/@{latt},{long},10.0z' if latt and long else None
        embed = discord.Embed(title='IPv4 Geolocation Lookup Result', url=url, color=MessageType.POSITIVE.value)

        name_values = [('IP', confirmed_ip), 
            ('City', city), ('Region', region), ("Postal Code", zip), ('Country', country), ('Timezone', timezone),
            ('Service Provider', isp), ('Organization', org), ('Autonomous System', a_system),
            ('Proxy', is_proxy), ('Mobile', is_mobile), ('Cached Result', is_cached), 
            ('Coordinates', f'{round(float(latt), 4)}, {round(float(long), 4)}')]
        for pairing in name_values:
            if pairing[1] != None:
                value_string = str(pairing[1])
                is_inline = len(value_string) < 20
                embed.add_field(name=pairing[0], value=value_string, inline=is_inline)

        embed.set_footer(text='Accuracy of IP geolocation lookup may vary per service that is used. This result may not be correct, for some addresses.')
        await command.get_channel().send(embed=embed)

    # if it is a bad response
    else:
        await command.get_channel().send(embed=Util.create_simple_embed(f'Unknown error processing request. Not a valid IPv4 address? Status {response.get("status")}', MessageType.FATAL))


@bot.command(name='math', hidden=False,
    brief='Do some math',
    usage='[simplify|factor|derive|integrate|zeroes|tangent|cos|sin|tan|arccos|arcsin|arc|tan|abs|log] [expression]',
    description='Do some math')
async def command_math(context: commands.Context):
    command = Command(context.message)
    operation = None
    if command.get_part(1) in ['simplify', 'factor', 'derive', 'integrate', 'zeroes', 'tangent', 'area', 'cos', 'sin', 'tan', 'arccos', 'arcsin', 'arctan', 'abs', 'log']:
        operation = command.get_part(1)
    expression = command.get_command_from(2)
    expression = expression.replace('/','(over)').replace('log','l')

    if operation == None or expression == '':
        await command.get_channel().send(embed=Util.create_simple_embed(f'Enter a valid operation and expression.', MessageType.NEGATIVE))
        return
    
    (response, mime, code) = await Util.http_get_thinking(f'https://newton.now.sh/api/v2/{operation}/{expression}', context)
    
    if (print_debug_if_needed(command, response)):
        return
    
    # this API does not return 400 when it is a bad request...
    if mime == ResponseType.JSON and code == 200:
        result = response.get('result')
        confirmed_expression = response.get('expression')
        await command.get_channel().send(f'**{operation.capitalize()}: {confirmed_expression}**```{result}```')

    # if it is a bad response
    else:
        await command.get_channel().send(embed=Util.create_simple_embed(f'Unknown error processing request. Is it a valid request? Code {code}', MessageType.FATAL))


# start from https://github.com/public-apis/public-apis#science--math

# #####################################
# Print raw json if needed
# #####################################

def print_debug_if_needed(command: Command, response: dict | str):
    if command.does_arg_exist('raw'):
        import json
        try:
            pretty_dump = json.dumps(response, indent=4)
            with open(fr"logs/command.{command.get_part(0)}.output.json", "w") as text_file:
                text_file.write(pretty_dump)
            print("File written")
        except:
            print("Failed to write dump")
        return True
    else:
        return False
    

bot.run(os.getenv('BOT_TOKEN'))