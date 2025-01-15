import datetime
import json
import os
import discord
from discord.ext import commands
from classes.media_preset import MediaPreset
from classes.text_command import TextCommand
from state import Program, Utility

class MediaCog(commands.Cog):
    _default_channel_type: str
    media_presets: dict[str, MediaPreset]

    def __init__(self):
        self._default_channel_type = "jukebox"
        self.media_presets = {}
            

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"MediaCog.on_ready(): We have logged in as {Program.bot.user}")

        filename = f"{Program.SETTINGS_DIRECTORY_PATH}/{Program.MEDIA_PRESETS_FILE_NAME}"
        if not os.path.exists(Program.SETTINGS_DIRECTORY_PATH):
            os.makedirs(Program.SETTINGS_DIRECTORY_PATH)
        if not os.path.isfile(filename):
            self.write_media_presets()
        self.load_media_presets()


    # #####################################
    # Commands
    # #####################################


    @commands.command(name="stream", aliases=["listen", "queue"], hidden=False, 
        brief="Play some media",
        usage=f"[preset_name] ... NOTE: use preset command to get the list of available media")
    async def command_stream(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=False, is_whisper_command=False):
            return
        
        command = TextCommand(context)
        preset_name = command.get_part(1)
        if not preset_name in self.media_presets.keys():
            await context.reply(f"`{preset_name}` is not a media preset.")
            return
        
        media_preset = self.media_presets.get(preset_name, None)
        protocol = media_preset.url.split('://')[0].lower()
        if not protocol in Program.WHITELISTED_PROTOCOLS:
            await context.send(f"Bad input. Must be a protocol in `{', '.join(Program.WHITELISTED_PROTOCOLS)}`")
            return
        
        # Find target voice channel
        voice_state = context.author.voice
        if voice_state == None:
            await context.reply(f"No voice state")
            return
        voice_channel = context.author.voice.channel
        if voice_channel == None:
            await context.reply("You must be in a voice channel")
            return
        
        source = await self.get_stream_from_path(media_preset.url)
        await self.join(context, voice_channel)
        context.voice_client.play(source, after=lambda e: print(f"Player error: {e}") if e else None)
        await context.send(f"Now playing: {media_preset.display_name}")


    @commands.command(name='playlist', aliases=['pl'], hidden=False, brief='Show the playlist queue')
    async def command_playlist(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=False, is_whisper_command=False):
            return
        
        i = 1
        queued_media: list[MediaPreset] = Program.guild_instances.get(context.guild.id).queued_media
        for media in queued_media:
            queue_text += f"{i}: {media.display_name}"
            i = i + 1
        embed = discord.Embed(title="Current Media Queue", description=queue_text)
        await context.send(embed=embed)


    @commands.command(name="presets", aliases=["preset"], hidden=False, brief="Show the list of available media presets")
    async def command_presets(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=False):
            return
        
        self.load_media_presets()
        preset_list = ""
        for key, preset in self.media_presets.items():
            preset_list += f"{preset.name} ({preset.display_name}): {preset.url}\n"
        await context.send(f"**The following presets are available when requesting media streams in the format `{Program.command_character}stream --preset=<preset_id_name>`:**\n```{preset_list}```")
        

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
            

    def write_media_presets(self):
        filename = f"{Program.SETTINGS_DIRECTORY_PATH}/{Program.MEDIA_PRESETS_FILE_NAME}"
        data = {"presets": list(map(lambda x: x[1].as_dict(), self.media_presets.items()))}
        
        with open(filename, "w") as file:
            json.dump(data, file, indent=4)
            print(f"Wrote to {filename} at {datetime.datetime.now()}")
                

    def load_media_presets(self) -> bool:
        filename = f"{Program.SETTINGS_DIRECTORY_PATH}/{Program.MEDIA_PRESETS_FILE_NAME}"
        if os.path.isfile(filename):
            with open(filename) as file:
                settings = json.load(file)
                media_presets = settings.get("presets", [])
                for mp in media_presets:
                    preset_name = mp.get("name", None)
                    if preset_name != None:
                        self.media_presets[preset_name] = MediaPreset(
                            mp.get("name"),
                            mp.get("display_name"),
                            mp.get("url"),
                            mp.get("is_opus")
                        )
                    else:
                        print(f"Invalid MediaPreset from file: {preset_name}")
                print(f"Loaded {filename} at {datetime.datetime.now()}")
        else:
            print(f"Filepath does not exist: {filename}")
            self.write_media_presets()
