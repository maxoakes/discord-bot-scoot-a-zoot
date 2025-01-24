import datetime
import json
import os
import discord
from discord.ext import commands
from classes.radio_station import RadioStation
from classes.text_command import TextCommand
from state import Program, Utility

class MediaCog(commands.Cog):
    _default_channel_type: str
    _settings_filename: str
    radio_stations: dict[str, RadioStation]

    def __init__(self):
        self._default_channel_type = "jukebox"
        self._settings_filename = f"{Program.SETTINGS_DIRECTORY_PATH}/{Program.RADIO_STATIONS_FILE_NAME}"
        self.radio_stations = {}
            

    @commands.Cog.listener()
    async def on_ready(self):
        Program.log(f"MediaCog.on_ready(): We have logged in as {Program.bot.user}",0)

        if Program.use_database:
            self.load_radio_stations_from_database()
            Program.log(f"Loaded {len(self.radio_stations)} saved radio stations from database.",0)
        else:
            if not os.path.exists(Program.SETTINGS_DIRECTORY_PATH):
                os.makedirs(Program.SETTINGS_DIRECTORY_PATH)

            # check if the radio stations settings file exists
            if not os.path.exists(self._settings_filename):
                # if it does not, create the file
                self.write_radio_stations_to_json()
                Program.log(f"Created empty {Program.RADIO_STATIONS_FILE_NAME}.",1)
            else:
                # if it does read it and load
                self.load_radio_stations_from_json()
                Program.log(f"Loaded {len(self.radio_stations)} saved radio station(s) from json file.",0)

        # show radio stations in console
        for n, r in self.radio_stations.items():
            Program.log(f"  {n}: {json.dumps(r.as_dict())}",0)


    # #####################################
    # Commands
    # #####################################

    @commands.command(name="stream", aliases=["listen", "queue", "play"], hidden=False, 
        brief="Play some media",
        usage=f"[preset_name] ... NOTE: use preset command to get the list of available media")
    async def command_stream(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=False, is_whisper_command=False):
            return
        
        # Get the requested radio station name
        command = TextCommand(context)
        preset_name = command.get_part(1)
        if not preset_name in self.radio_stations.keys():
            await context.reply(f"`{preset_name}` is not a media preset.")
            return
        
        # Get the radio station url
        radio_station = self.radio_stations.get(preset_name, None)
        protocol = radio_station.url.split('://')[0].lower()
        if not protocol in Program.WHITELISTED_PROTOCOLS:
            await context.reply(f"Bad input. Must be a protocol in `{', '.join(Program.WHITELISTED_PROTOCOLS)}`")
            return
        
        # Find target voice channel
        voice_channel = context.author.voice.channel
        if voice_channel == None:
            await context.reply("You must be in a voice channel")
            return
        
        async with context.typing():
            if context.voice_client and context.voice_client.is_playing():
                Program.log(f"Voice client in {context.guild.name} is already playing auto. Stopping to play another...",1)
                context.voice_client.stop()

            # Find the media and play
            source = await self.get_stream_from_path(radio_station.url)
            await self.join(context, voice_channel)
            context.voice_client.play(source, after=lambda e: Program.log(f"Media Player error: {e}",3) if e else None)
        await context.send(f"Now playing: `{radio_station.display_name}`")


    @commands.command(name="stop", hidden=False, brief="Stop and disconnect radio station")
    async def command_stop(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=False):
            return
        
        if context.voice_client != None:
            Program.log(f"Voice client in {context.guild.name} is already playing auto. Stopping to play another...",1)
            context.voice_client.stop()
            await context.voice_client.disconnect()
            await context.send(f"Turning off the radio station...")
        else:
            await context.reply(f"The radio is currently not playing.")
        

    @commands.command(name="stations", hidden=False, brief="Refresh local cache from disk and display them")
    async def command_stations(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=False):
            return
        
        command = TextCommand(context)
        if command.get_part(1) == "reload":
            async with context.typing():
                if Program.use_database:
                    self.load_radio_stations_from_database()
                else:
                    self.load_radio_stations_from_json()

        station_list = list(map(lambda x: f"[{x[1].name}] {x[1].display_name}", self.radio_stations.items()))
        station_string = "\n".join(station_list)
        await context.send(f"**The following radio stations are available:**\n```{station_string} ```")


    # #########################
    # Helper Functions
    # #########################

    async def join(self, ctx: commands.Context, channel: discord.VoiceChannel):
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)
        await channel.connect()


    async def get_stream_from_path(self, source_string: str, is_opus=False):
        protocol = source_string.split('://')[0].lower()
        if protocol == Program.FILE_PROTOCOL_PREFIX:
            return discord.FFmpegPCMAudio(source=source_string[len(Program.FILE_PROTOCOL_PREFIX):])
        else:
            if is_opus:
                return await discord.FFmpegOpusAudio.from_probe(source_string, **Program.FFMPEG_OPTIONS, method='fallback')
            else:
                return discord.FFmpegPCMAudio(source=source_string, **Program.FFMPEG_OPTIONS)
            

    # #########################
    # I/O functions
    # #########################

    def write_radio_stations_to_json(self):
        data = {"presets": list(map(lambda x: x[1].as_dict(), self.radio_stations.items()))}
        with open(self._settings_filename, "w") as file:
            json.dump(data, file, indent=4)
            Program.log(f"Wrote to {self._settings_filename}",0)
                

    def load_radio_stations_from_json(self) -> bool:
        with open(self._settings_filename) as file:
            settings = json.load(file)
            radio_stations = settings.get("presets", [])
            self.radio_stations.clear()
            for mp in radio_stations:
                preset_name = mp.get("name", None)
                if preset_name != None:
                    self.radio_stations[preset_name] = RadioStation(mp.get("name"), mp.get("display_name"), mp.get("url"), mp.get("is_opus"))
                else:
                    Program.log(f"Invalid RadioStation from file: {preset_name}",2)
            Program.log(f"Loaded {self._settings_filename}",0)


    def update_radio_station_to_database(self, name: str, display_name: str, url: str, opus: bool):
        return Program.call_procedure_return_scalar("insert_or_update_radio_station", (name, display_name, url, opus))
    

    def load_radio_stations_from_database(self):
        rows = Program.run_query_return_rows("SELECT unique_name, display_name, url, is_opus FROM radio_stations")
        self.radio_stations.clear()
        for unique_name, display_name, url, is_opus in rows:
            self.radio_stations[unique_name] = RadioStation(unique_name, display_name, url, is_opus)
