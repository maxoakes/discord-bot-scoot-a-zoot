import datetime
import os
import discord
from discord.ext import commands
from classes.text_command import TextCommand
from state import MessageType, Program, Utility

class ToolsCog(commands.Cog):

    _default_channel_type: str

    def __init__(self):
        self._default_channel_type = "command"


    @commands.Cog.listener()
    async def on_ready(self):
        Program.log(f"ToolsCog.on_ready(): We have logged in as {Program.bot.user}")
    

    # #####################################
    # Commands
    # #####################################

    # https://api.mcsrvstat.us/
    @commands.command(name="minecraft", aliases=["mc"], hidden=False, 
        brief="Get the status of a Minecraft server", 
        usage="[server address]",
        description="Get the status of a Minecraft server. If the server is online, get all significant information.")
    async def command_minecraft(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=False):
            return

        command = TextCommand(context)
        address = command.get_command_from(1)
        if Utility.is_null_or_whitespace(address):
            context.reply(Program.get_help_instructions("minecraft"))
            return
        query_url = f"https://api.mcsrvstat.us/2/{address}"
        (response, mime, code) = await Utility.http_get_thinking(query_url, context)
        
        if Utility.is_200(code):
            # required elements
            full_address = f"{response.get('ip', '?.?.?.?')}:{response.get('port', '?????')}"
            is_online = response.get("online", False)
            status = "Online" if is_online else "Offline"
            server_name = response.get("hostname") if response.get("hostname", False) else "Minecraft Server"
            embed_color = MessageType.POSITIVE.value if is_online else MessageType.NEGATIVE.value

            # craft the embed
            embed = discord.Embed(title=server_name, color=embed_color)
            embed.add_field(name="Address", value=full_address)
            embed.add_field(name="Status", value=status)

            if is_online:
                players_curr = response.get("players").get("online")
                players_max = response.get("players").get("max")
                embed.add_field(name="Player Count", value=f"{players_curr} of {players_max}")
                
                motd = ""
                for string in response.get("motd").get("clean"):
                    motd = motd + string + "\n"
                embed.add_field(name="Message of the Day", value=motd, inline=False)

                embed.add_field(name="Version", value=response.get("version", "Unknown Version"))
                if response.get("mods"):
                    embed.add_field(name="Number of Mods", value=len(response.get("mods").get("names", [])), inline=False)

            await context.send(embed=embed)

        elif Utility.is_400(code):
            await context.reply(Program.get_client_error_user_response(code))
        else:
            await context.reply(Program.get_server_error_user_response(code))
            await Program.write_dev_log(Program.get_http_control_server_response(code, context, query_url))


    # https://dictionaryapi.dev/
    @commands.command(name="word", hidden=False, aliases=["dict", "dictionary", "def", "define"],
        brief="Get the definition(s) of a word", 
        usage="[word]",
        description="Get the definition(s) of a word")
    async def command_word(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=False):
            return
        
        command = TextCommand(context)
        word = command.get_command_from(1)
        if Utility.is_null_or_whitespace(word):
            context.reply(Program.get_help_instructions("word"))
            return
        
        query_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        (response, mime, code) = await Utility.http_get_thinking(query_url, context)
        
        if Utility.is_200(code):
            for usage in response:
                # get the word
                if not usage.get("word"):
                    continue
                this_word = usage.get("word").capitalize()

                # for each meaning, get each definition. Each meaning will have its own embed
                for meaning in usage.get("meanings", []):
                    part = meaning.get("partOfSpeech")
                    embed = discord.Embed(title=f"{this_word} ({part})", url=usage.get("sourceUrls", [None])[0], color=MessageType.POSITIVE.value)
                    embed.add_field(name="Phonetics", value=usage.get("phonetic"), inline=False)

                    # for each definition, add a field in the embed
                    i = 0
                    for i, definition in enumerate(meaning.get("definitions")):
                        name = f"{i+1}. Definition"
                        d = definition.get("definition")
                        e = definition.get("example")

                        # the value will be the definition, and additionally an example, if one is provided
                        value = f"{d}\n - Example: *{e}*\n" if e else f"{d}"

                        embed.add_field(name=name, value=value, inline=False)
                    embed.add_field(name="Source", value=usage.get("sourceUrls", ["None available"])[0], inline=False)
                    await context.send(embed=embed)

        elif Utility.is_400(code):
            await context.reply(Program.get_client_error_user_response(code))
        else:
            await context.reply(Program.get_server_error_user_response(code))
            await Program.write_dev_log(Program.get_http_control_server_response(code, context, query_url))


    # https://color.serialif.com/#anchor-request
    # note: not using alpha channel ability with this API because the response is not consistent with non-alpha color response
    @commands.command(name="color", hidden=False,
        brief="Enter a color for its RGB, HSL, hex values and closest name", 
        usage="(name [name of color]) OR (hex [hexidecimal value]) OR (rgb [0..255] [0..255] [0..255]) OR (hsl [0..255] [0..100] [0..100])",
        description="Enter a color for its RGB, HSL, hex values and closest name")
    async def command_color(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=False):
            return
        
        command = TextCommand(context)
        value_type = command.get_part(1)
        query_url = "https://color.serialif.com/"

        # parse command for color components
        # if it is a color code of ints
        if value_type in ["rgb", "hsl", "hsl"]:
            values = (command.get_part(2), command.get_part(3), command.get_part(4))
            query_url = query_url + f"{value_type}={values[0]},{values[1]},{values[2]}"
        # if it is a name for a color
        elif value_type in ["name", "word", "keyword"]:
            query_url = query_url + f"keyword={command.get_command_from(2)}"
        # if it is a hex or hex alpha
        elif value_type in ["hex"]:
            query_url = query_url + f"{command.get_part(2).replace('0x', '').replace('#', '')}"
        # if the input params were bad
        else:
            await context.reply(Program.get_help_instructions("color"))
            return

        # when everything is all good, make the request
        (response, mime, code) = await Utility.http_get_thinking(query_url, context)
        status = response.get("status")
        
        # this API does not return 400 when it is a bad request...
        if status == "success":
            # create the embed describing the requested color
            base_keyword = response.get("base", {}).get("keyword", "").capitalize()
            base_rgb = response.get("base", {}).get("rgb", {}).get("value")
            base_hsl = response.get("base", {}).get("hsl", {}).get("value")
            base_hex = response.get("base", {}).get("hex", {}).get("value")

            base_value = int(f"0x{base_hex[1:]}", 16)
            base_title_available = base_keyword != ""
            base_title = base_keyword if base_title_available else base_rgb
            base_embed = discord.Embed(title=f"Requested: {base_title}", color=base_value)

            if base_title_available:
                base_embed.add_field(name="Closest Name", value=base_keyword, inline=False)
            base_embed.add_field(name="Red, Blue, Green", value=base_rgb, inline=False)
            base_embed.add_field(name="Hue, Saturation, Lightness", value=base_hsl, inline=False)
            base_embed.add_field(name="Hexidecimal", value=base_hex, inline=False)
            await context.send(embed=base_embed)

            # create an embed for the complementary color
            comp_keyword = response.get("complementary", {}).get("keyword", "").capitalize()
            comp_rgb = response.get("complementary", {}).get("rgb", {}).get("value")
            comp_hsl = response.get("complementary", {}).get("hsl", {}).get("value")
            comp_hex = response.get("complementary", {}).get("hex", {}).get("value")

            comp_value = int(f"0x{comp_hex[1:]}", 16)
            comp_title_available = comp_keyword != ""
            comp_title = comp_keyword if comp_title_available else comp_rgb
            comp_embed = discord.Embed(title=f"Complementary: {comp_title}", color=comp_value)

            if comp_title_available:
                comp_embed.add_field(name="Closest Name", value=comp_keyword, inline=False)
            comp_embed.add_field(name="Red, Blue, Green", value=comp_rgb, inline=False)
            comp_embed.add_field(name="Hue, Saturation, Lightness", value=comp_hsl, inline=False)
            comp_embed.add_field(name="Hexidecimal", value=comp_hex, inline=False)
            await context.send(embed=comp_embed)

        elif status == "error":
            await context.reply(f"Got an error response. Perhaps it was not a valid color. Message: {response.get('error', {}).get('message')}")
        else:
            await context.reply(f"Unknown error. Is the endpoint server down? ({code}): {response}")
            await Program.write_dev_log(Program.get_http_control_server_response(code, context, query_url, response))


    # https://corporatebs-generator.sameerkumar.website/
    @commands.command(name="buzz", hidden=False,
        brief="Generate a buzzword tech phrase",
        description="Generate a buzzword tech phrase")
    async def command_buzz(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=False):
            return
        
        query_url = "https://corporatebs-generator.sameerkumar.website/"
        (response, mime, code) = await Utility.http_get_thinking(query_url, context)
        
        # this API does not return 400 when it is a bad request...
        if Utility.is_200(code):
            phrase = response.get("phrase")
            await context.send(f"*I present*... **{phrase}**")

        elif Utility.is_400(code):
            await context.reply(Program.get_client_error_user_response(code))
        else:
            await context.reply(Program.get_server_error_user_response(code))
            await Program.write_dev_log(Program.get_http_control_server_response(code, context, query_url))


    # https://uselessfacts.jsph.pl/
    @commands.command(name="fact", hidden=False,
        brief="Generate a random fun-fact",
        usage="(--de)",
        description="Generate a random fun-fact. Also supports results in German.")
    async def command_fact(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=False):
            return
        
        command = TextCommand(context)
        suffix = "?language=de" if command.does_arg_exist("de") else ""
        query_url = f"https://uselessfacts.jsph.pl/api/v2/facts/random{suffix}"
        (response, mime, code) = await Utility.http_get_thinking(query_url, context)
        
        if Utility.is_200(code):
            fact = response.get("text", "This API is broken")
            await context.send(f"**Fun Fact:** {fact}")

        elif Utility.is_400(code):
            await context.reply(Program.get_client_error_user_response(code))
        else:
            await context.reply(Program.get_server_error_user_response(code))
            await Program.write_dev_log(Program.get_http_control_server_response(code, context, query_url))


    # https://v2.jokeapi.dev/
    @commands.command(name="joke", hidden=False,
        brief="Get a joke",
        usage="[programming|dark|pun|spooky|christmas] (--nsfw) (--religious) (--political) (--racist) (--sexist) (--explicit) (--search=[string]) (--lang=[en|es|de|fr|cs|pt])",
        description="Get a joke. Use --flags to blacklist types of jokes. Not specifying a category will yield any type of joke.")
    async def command_joke(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=False):
            return

        command = TextCommand(context)

        # get the list of request categories
        categories = []
        i = 1
        while command.get_part(i) != "":
            if command.get_part(i) in ["programming", "dark", "pun", "spooky", "christmas"]:
                categories.append(command.get_part(i))
            i = i + 1
        if len(categories) == 0:
            categories = ["Any"]
        categories_string = ",".join(categories)

        # get all blacklisted categories
        blacklisted = []
        for flag in ["religious", "political", "racist", "sexist", "explicit"]:
            if command.does_arg_exist(flag):
                blacklisted.append(flag)
        blacklist_string = f"blacklistFlags={','.join(blacklisted)}&" if len(blacklisted) > 0 else ""

        # get the language parameter
        lang_string = ""
        input_lang = command.get_arg("lang")
        if input_lang in ["en", "es", "de", "fr", "cs", "pt"]:
            lang_string = f"lang={input_lang}&"

        # get any string to search
        search_string = ""
        input_search = command.get_arg("search")
        if input_search:
            search_string = f"contains={input_search}&"

        query_url = f"https://v2.jokeapi.dev/joke/{categories_string}?{lang_string}{blacklist_string}{search_string}"
        (response, mime, code) = await Utility.http_get_thinking(query_url, context)
        
        if Utility.is_200(code):
            preface = "Here is a joke:\n"
            joke_type = response.get("type")
            if joke_type == "single":
                joke = response.get("joke")
                await context.send(f"{preface}*{joke}*")
            elif joke_type == "twopart":
                setup = response.get("setup")
                delivery = response.get("delivery")
                await context.send(f"{preface}*{setup}\n||{delivery}||*")
            else:
                if response.get("code") == 106: # 106 ?= no joke found
                    await context.reply("No joke matching the selected criteria. soz")
                else:
                    await context.reply(f"The joke was too good; it broke the API. code={response.get('code', '???')}")
                    
        elif Utility.is_400(code):
            await context.reply(Program.get_client_error_user_response(code))
        else:
            await context.reply(Program.get_server_error_user_response(code))
            await Program.write_dev_log(Program.get_http_control_server_response(code, context, query_url))


    # https://geokeo.com/
    @commands.command(name="geo", hidden=False, aliases=["loc", "location", "geography"],
        brief="Get geographical information from an input",
        usage="[any location input type] (--limit=[number])",
        description="Get geographical information from an input")
    async def command_geo(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=False):
            return
        
        command = TextCommand(context)
        input_string = command.get_command_from(1)
        result_limit = int(command.get_arg("limit", default=3))
        if Utility.is_null_or_whitespace(input_string):
            await context.reply(Program.get_help_instructions("geo"))
            return
        
        query_url = f"https://geokeo.com/geocode/v1/search.php?q={input_string}?&api={os.getenv('GEOKEO_TOKEN')}"
        try:
            (response, mime, code) = await Utility.http_get_thinking(query_url, context)
            status = response.get("status", "ok")

            # this API only returns 200 code...
            if status == "ok":
                for result in response.get("results", [])[:result_limit]:
                    geo_class = result.get("class", "Location").capitalize()
                    geo_type = result.get("type", "").capitalize()
                    address: dict = result.get("address_components", {})
                    coords: dict = result.get("geometry").get("location")
                    url = f"https://www.google.com/maps/@{coords.get('lat')},{coords.get('lng')},15.0z"
                    embed = discord.Embed(title=f"{geo_class} Information", url=url, color=MessageType.POSITIVE.value)

                    name_values = [("Class", geo_class), ("Type", geo_type)]
                    address_order = ["name", "island", "neighbourhood", "street", "subdistrict", "district", "city", "state", "postcode", "country"]
                    for component in address_order:
                        value = address.get(component)
                        if value:
                            name_values.append((component.capitalize(), address.get(component)))

                    Utility.build_embed_fields(embed, name_values)
                    embed.add_field(name="Coordinates", value=f"{round(float(coords.get('lat')), 4)}, {round(float(coords.get('lng')), 4)}", inline=False)
                    await context.send(embed=embed)

            elif status == "ZERO_RESULTS":
                await context.reply(Program.get_client_error_user_response(status))
            else:
                await context.reply(Program.get_server_error_user_response(status))
                await Program.write_dev_log(Program.get_http_control_server_response(code, context, query_url, status))
        except:
            await context.reply(Program.get_server_error_user_response("Error in API response"))
            await Program.write_dev_log(Program.get_http_control_server_response(None, context, query_url, "Possible malformed JSON"))


    # https://api.techniknews.net/ipgeo/
    @commands.command(name="ip", hidden=False,
        brief="Get (possibly) correct location statistics from an IPv4 address",
        usage="[IPv4 address]",
        description="Get (possibly) correct location statistics from an IPv4 address")
    async def command_ip(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=False):
            return
        
        command = TextCommand(context)
        ip = command.get_command_from(1)
        if Utility.is_null_or_whitespace(ip):
            await context.reply(Program.get_help_instructions("ip"))
            return
        
        query_url = f"https://api.techniknews.net/ipgeo/{ip}"
        (response, mime, code) = await Utility.http_get_thinking(query_url, context)
        status = response.get("status", "success")
        
        # this API only returns 200 code...
        if status == "success":
            latt = response.get("lat", 0)
            long = response.get("lon", 0)

            url = f"https://www.google.com/maps/@{latt},{long},15.0z" if latt and long else None
            embed = discord.Embed(title="IPv4 Geolocation Lookup Result", url=url, color=MessageType.POSITIVE.value)

            name_values = [
                ("IP", response.get("ip")), 
                ("City", response.get("city")), 
                ("Region", response.get("regionName")), 
                ("Postal Code", response.get("zip")), 
                ("Country", response.get("country")), 
                ("Timezone", response.get("timezone")),
                ("Service Provider", response.get("isp")), 
                ("Organization", response.get("org")), 
                ("Autonomous System", response.get("as")),
                ("Proxy", response.get("proxy")), 
                ("Mobile", response.get("mobile")), 
                ("Cached Result", response.get("cached")), 
                ("Coordinates", f"{round(float(latt), 4)}, {round(float(long), 4)}")]
            Utility.build_embed_fields(embed, name_values)

            embed.set_footer(text="Note that accuracy of IP geolocation lookup may vary per service that is used. This result may not be correct for some addresses.")
            await context.send(embed=embed)
        else:
            if response.get("message", "invalid ip"):
                await context.reply(Program.get_client_error_user_response(response.get("message")))
            else:
                await context.reply(Program.get_server_error_user_response(response.get("message")))
                await Program.write_dev_log(Program.get_http_control_server_response(code, context, query_url, response.get("message")))



    # https://newton.vercel.app/
    @commands.command(name="math", hidden=False,
        brief="Do some math",
        usage="[simplify|factor|derive|integrate|zeroes|tangent|cos|sin|tan|arccos|arcsin|arc|tan|abs|log] [expression]",
        description="Do some math")
    async def command_math(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=False):
            return
        
        command = TextCommand(context)
        operation = None
        if command.get_part(1) in ["simplify", "factor", "derive", "integrate", "zeroes", "tangent", "area", "cos", "sin", "tan", "arccos", "arcsin", "arctan", "abs", "log"]:
            operation = command.get_part(1)
        expression = command.get_command_from(2)
        expression = expression.replace("/","(over)").replace("log","l")

        if Utility.is_null_or_whitespace(operation) or Utility.is_null_or_whitespace(expression):
            await context.reply(Program.get_help_instructions("math"))
            return
        
        query_url = f"https://newton.now.sh/api/v2/{operation}/{expression}"
        (response, mime, code) = await Utility.http_get_thinking(query_url, context)
        
        if Utility.is_200(code):
            result = response.get("result")
            confirmed_expression = response.get("expression")
            await context.send(f"**{operation.capitalize()}: {confirmed_expression}**```{result}```")

        elif Utility.is_400(code):
            await context.reply(Program.get_client_error_user_response(code))
        else:
            await context.reply(Program.get_server_error_user_response(code))
            await Program.write_dev_log(Program.get_http_control_server_response(code, context, query_url))


    # https://docs.aviationapi.com/#tag/airports
    @commands.command(name="airport", hidden=False, aliases=["ap", "av"],
        brief="Get basic airport statistics given a code",
        usage="[list of ICAO or FAA identifiers separated by spaces]",
        description="Get basic airport statistics given a code")
    async def command_airport(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=False):
            return
        
        command = TextCommand(context)
        param = command.get_command_from(1).replace(", ",",").replace(" ",",")
        if Utility.is_null_or_whitespace(param):
            await context.reply(Program.get_help_instructions("airport"))
            return

        query_url = f"https://api.aviationapi.com/v1/airports?apt={param}"
        (response, mime, code) = await Utility.http_get_thinking(query_url, context)
        
        if Utility.is_200(code):
            for (key, entry) in list(response.items()):
                if len(entry) == 0:
                    await context.reply(f"Could not find anything given the ID `{key}`. Note this command is for US airfields only.")
                    continue
                info: dict = entry[0]
                name = info.get("facility_name", "Unknown Name")
                airport_type = info.get("type", "Unknown Type")
                title = f"{name} ({airport_type})"
                embed = discord.Embed(title=title, color=MessageType.POSITIVE.value)

                name_values = [
                    ("NOTAM Identity", info.get("notam_facility_ident")),
                    ("City", info.get("city")), 
                    ("County", info.get("county")), 
                    ("State", info.get("state")), 
                    ("Region", info.get("region")), 
                    ("Ownership", info.get("ownership")), 
                    ("Elevation", info.get("elevation")),
                    ("Magnetic Variation", info.get("magnetic_variation")), 
                    ("VFR Sectional", info.get("vfr_sectional")), 
                    ("Responsible ARTCC", info.get("responsible_artcc_name")), 
                    ("Lighting Schedule", info.get("lighting_schedule")), 
                    ("Beacon Schedule", info.get("beacon_schedule")),
                    ("Military Landing Available", info.get("military_landing")),
                    ("Military Joint Use", info.get("military_joint_use")),
                    ("Control Tower", info.get("control_tower")),
                    ("UNICOM", info.get("unicom")),
                    ("CTAF", info.get("ctaf")),
                    ("Latitude", info.get("latitude")), 
                    ("Longitude", info.get("longitude")),
                    ("Info Last Updated", info.get("effective_date"))
                ]

                Utility.build_embed_fields(embed, name_values)
                await context.send(embed=embed)

        elif Utility.is_400(code):
            await context.reply(Program.get_client_error_user_response(code))
        else:
            await context.reply(Program.get_server_error_user_response(code))
            await Program.write_dev_log(Program.get_http_control_server_response(code, context, query_url))


    # https://openweathermap.org/current
    @commands.command(name="weather", hidden=False, aliases=["w"],
        brief="Get the current weather for a location",
        usage="(zip [ZIP code] [country abbr]) OR (city [city], (state abbr), [country abbr])",
        description="Get the current weather for a location")
    async def command_weather(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=False):
            return
        
        command = TextCommand(context)
        param = command.get_command_from(2)
        method = command.get_part(1).lower()
        if not method in ["zip", "city"]:
            await context.reply(Program.get_help_instructions("weather"))
            return

        search_query = "q=" if method == "city" else "zip="
        search_query = search_query + param
        query_url = f"https://api.openweathermap.org/data/2.5/weather?{search_query}&units=imperial&appid={os.getenv('OPENWEATHER_TOKEN')}"
        (response, mime, code) = await Utility.http_get_thinking(query_url, context)
        
        if Utility.is_200(code):
            location = f"{response.get('name', 'Unknown')}, {response.get('sys', {}).get('country', 'Unknown')}"
            url = None
            coordinates = response.get("coord", {})
            if coordinates:
                url = f"https://www.ventusky.com/?p={coordinates.get('lat')};{coordinates.get('lon')};7&l=temperature-2m"

            embed = discord.Embed(title=f"Current Weather for {location}", url=url, color=MessageType.POSITIVE.value)

            # get the appropriate icon, given by the API response
            # See https://openweathermap.org/weather-conditions
            name_values = []
            weather_comp = response.get("weather", [{}])[0]
            if weather_comp:
                name_values.append(("Description", weather_comp.get("description", "Unknown").capitalize(), False))
                embed.set_thumbnail(url=f"https://openweathermap.org/img/wn/{weather_comp.get('icon', '01d')}@2x.png")

            # get temperature stats
            temperature_suffix = " °F"
            main_comp = response.get("main", {})
            if main_comp:
                name_values.append(("Temperature", f"{main_comp.get('temp')}{temperature_suffix}"))
                name_values.append(("Feels Like", f"{main_comp.get('feels_like')}{temperature_suffix}"))
                name_values.append(("Low", f"{main_comp.get('temp_min')}{temperature_suffix}"))
                name_values.append(("High", f"{main_comp.get('temp_max')}{temperature_suffix}"))
                name_values.append(("Pressure", f"{main_comp.get('pressure')} mb"))
                name_values.append(("Humidity", f"{main_comp.get('humidity')}%"))

            # get visibility
            visibility = response.get("visibility")
            if visibility != None:
                visibility = f"{visibility}m" if visibility < 10000 else "Greater than 10km"
            name_values.append(("Visibility", visibility))

            # get wind conditions
            wind = response.get("wind", {})
            if wind:
                speed = wind.get("speed", "?")
                dir = wind.get("deg", "?")
                gust = wind.get("gust")
                wind_string = f"{Utility.deg_to_compass(dir)} @ {speed} mph "
                if gust: # do not append a gust mention if there is 0 gust, or if the field does not exist
                    wind_string = wind_string + f" with gusts of {gust} mph"
                name_values.append(("Winds", wind_string))

            clouds = response.get("clouds", {}).get("all")
            if clouds != None:
                name_values.append(("Cloud Coverage", f"{clouds}%", False))
            
            # get the sunrise/sunset times
            system_comp = response.get("sys", {})
            if system_comp:
                time_format = "%I:%M:%S %p"
                sunrise = system_comp.get("sunrise", 0)
                name_values.append(("Sunrise", datetime.datetime.fromtimestamp(sunrise).strftime(time_format) + " PST", True))
                sunset = system_comp.get("sunset", 0)
                name_values.append(("Sunset", datetime.datetime.fromtimestamp(sunset).strftime(time_format) + " PST", True))

            Utility.build_embed_fields(embed, name_values)
            await context.send(embed=embed)

        elif Utility.is_400(code):
            await context.reply(Program.get_client_error_user_response(code))
        else:
            await context.reply(Program.get_server_error_user_response(code))
            await Program.write_dev_log(Program.get_http_control_server_response(code, context, query_url))
