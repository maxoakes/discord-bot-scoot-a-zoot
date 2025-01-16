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
    radio_stations: dict[str, RadioStation]

    def __init__(self):
        self._default_channel_type = "jukebox"
        self.radio_stations = {}
            

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"MediaCog.on_ready(): We have logged in as {Program.bot.user}")

        filename = f"{Program.SETTINGS_DIRECTORY_PATH}/{Program.RADIO_STATIONS_FILE_NAME}"
        if not os.path.exists(Program.SETTINGS_DIRECTORY_PATH):
            os.makedirs(Program.SETTINGS_DIRECTORY_PATH)
        if not os.path.isfile(filename):
            self.write_radio_stations()
        self.load_radio_stations()


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
        
        if context.voice_client and context.voice_client.is_playing():
            print(f"Voice client in {context.guild.name} is already playing auto. Stopping to play another...")
            context.voice_client.stop()

        # Find the media and play
        source = await self.get_stream_from_path(radio_station.url)
        await self.join(context, voice_channel)
        context.voice_client.play(source, after=lambda e: print(f"Player error: {e}") if e else None)
        await context.send(f"Now playing: `{radio_station.display_name}`")


    @commands.command(name="stop", hidden=False, brief="Stop and disconnect radio station")
    async def command_stop(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=False):
            return
        
        if context.voice_client != None:
            print(f"Voice client in {context.guild.name} is already playing auto. Stopping to play another...")
            context.voice_client.stop()
            await context.voice_client.disconnect()
            await context.send(f"Turning off the radio station...")
        else:
            await context.reply(f"The radio is currently not playing.")
        


    @commands.command(name="stations", hidden=False, brief="Show the list of available radio stations")
    async def command_stations(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=False):
            return
        
        self.load_radio_stations()
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
            return discord.FFmpegPCMAudio(executable=os.getenv('FFMPEG_PATH'), source=source_string[len(Program.FILE_PROTOCOL_PREFIX):])
        else:
            if is_opus:
                return await discord.FFmpegOpusAudio.from_probe(source_string, executable=os.getenv('FFMPEG_PATH'), **Program.FFMPEG_OPTIONS, method='fallback')
            else:
                return discord.FFmpegPCMAudio(source=source_string, executable=os.getenv('FFMPEG_PATH'), **Program.FFMPEG_OPTIONS)
            

    def write_radio_stations(self):
        filename = f"{Program.SETTINGS_DIRECTORY_PATH}/{Program.RADIO_STATIONS_FILE_NAME}"
        data = {"presets": list(map(lambda x: x[1].as_dict(), self.radio_stations.items()))}
        
        with open(filename, "w") as file:
            json.dump(data, file, indent=4)
            print(f"Wrote to {filename} at {datetime.datetime.now()}")
                

    def load_radio_stations(self) -> bool:
        filename = f"{Program.SETTINGS_DIRECTORY_PATH}/{Program.RADIO_STATIONS_FILE_NAME}"
        if os.path.isfile(filename):
            with open(filename) as file:
                settings = json.load(file)
                radio_stations = settings.get("presets", [])
                for mp in radio_stations:
                    preset_name = mp.get("name", None)
                    if preset_name != None:
                        self.radio_stations[preset_name] = RadioStation(
                            mp.get("name"),
                            mp.get("display_name"),
                            mp.get("url"),
                            mp.get("is_opus")
                        )
                    else:
                        print(f"Invalid RadioStation from file: {preset_name}")
                print(f"Loaded {filename} at {datetime.datetime.now()}")
        else:
            print(f"Filepath does not exist: {filename}")
            self.write_radio_stations()
