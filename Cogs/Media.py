import asyncio
import discord
from discord.ext import commands
import youtube_search
from Command import Command
from Media.LinearPlaylist import LinearPlaylist, PlaylistAction
from Media.MediaManager import MediaManager
from Media.PlaylistRequest import PlaylistRequest
from Util import MessageType, Util

class Media(commands.Cog):
    MEDIA_PRESETS_PATH = r'Media/presets.csv'
    media_manager: MediaManager
    playlist: LinearPlaylist
    this_guild: discord.Guild
    possible_channel_names: list
    default_channel: discord.TextChannel = None
    bot: discord.Bot
    channel_selection: int

    def __init__(self, bot, channel_names, channel_selection=-1):
        self.bot = bot
        self.media_manager = MediaManager()
        self.playlist = LinearPlaylist(bot)
        self.possible_channel_names = channel_names
        self.channel_selection = channel_selection
            

    # on startup
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"We have logged in as {self.bot.user}")
        # select the server to manage
        print("Available Guilds:")
        for i, g in enumerate(self.bot.guilds):
            print(f"  [{i}] = {g.name} ({g.id})")
        
        try:
            selected_guild: int
            if self.channel_selection > -1:
                selected_guild = self.channel_selection
            else:
                selected_guild = input("Index Number Guild to manage: ")
            self.this_guild = self.bot.guilds[int(selected_guild)]
        except:
            print("ERROR, Could not properly parse input. Selecting first entry...")
            self.this_guild = self.bot.guilds[0]

        print(f"Now managing '{self.this_guild.name}' ({self.this_guild.id})")

        # attempt to find the default channel
        temp_default_channel = self.this_guild.system_channel

        # attempt to find the two types of channels for the purpose of this bot
        for channel in self.this_guild.text_channels:
            if channel.permissions_for(self.this_guild.me).send_messages:
                if channel.name in self.possible_channel_names:
                    self.default_channel = channel
            
        # if media channel is not found, attempt to assign a fallback channel that the users can send commands
        if self.default_channel == None:
            print(f"\tNo media channel found for {self.this_guild.name}, finding default")
            if temp_default_channel.permissions_for(self.this_guild.me).send_messages:
                self.default_channel = temp_default_channel
                print(f"I have found a default channel at {self.this_guild.name}/{channel.name}")
        if self.default_channel == None:
            print('WARNING, no default media request channel is accessible. This bot will not have full functionality.')

        # send opening message
        print(f"READY! Initialized for '{self.this_guild.name}' with default-channel='{self.default_channel}'")


    # #####################################
    # Manual Checks (does not use built-in cog command checks)
    # #####################################

    def is_command_channel(self, command: Command):
        return isinstance(command.get_channel(), discord.channel.DMChannel) or command.get_channel().id == self.default_channel.id
    

    def is_admin_author(self, command: Command):
        return True


    # #####################################
    # Commands
    # #####################################

    @commands.command(name='search', aliases=['lookup', 'query'], hidden=False, brief='Search a service for some media')
    async def command_search(self, context: commands.Context):
        command = Command(context.message)
        if not self.is_command_channel(command):
            print(f'{command.get_part(0)} failed check. Aborting.')
            return
        
        request = await self.service_search(command)
        if request:
            embed = await request.get_embed(MessageType.POSITIVE, pos=len(self.playlist.get_next_queue()))
            await self.default_channel.send(f"**Adding this search result to playlist queue:**", embed=embed)
            self.playlist.add_queue(request)
            await self.media_play()


    @commands.command(name='stream', aliases=['add', 'listen', 'queue'], hidden=False, brief='Add a specific URL to the playlist queue')
    async def command_stream(self, context: commands.Context):
        command = Command(context.message)
        if not self.is_command_channel(command):
            print(f'{command.get_part(0)} failed check. Aborting.')
            return
        
        source_string = command.get_command_from(1).strip()
        use_opus = command.does_arg_exist('opus')
        preset = command.get_arg('preset')
        if preset:
            # if there is a preset, get it from the presets file
            import csv
            try:
                with open(Media.MEDIA_PRESETS_PATH, newline='', encoding='utf-8') as file:
                    reader = csv.reader(file)
                    for row in reader:
                        # [preset, url, desc, use_opus]
                        if row[0].lower() == preset.lower():
                            source_string = row[1]
                            use_opus = row[3].lower() in Util.AFFIRMATIVE_RESPONSE
            except Exception as e:
                await command.get_message().channel.send(
                    f"How did this happen, {Util.get_author_mention()}?", 
                    embed=Util.create_simple_embed("An error occurred getting a the media presets, nothing will be added to the queue.", MessageType.FATAL))
                print(f'Error processing presets file: {e}')
        # if there was no source url or valid preset, it is a bad request
        if source_string == "" or (source_string.find('http') != 0 and source_string.find('file') != 0):
            await self.default_channel.send(embed=Util.create_simple_embed(f"Bad input. Must be an `http://`, `https://`, or `file://` protocol, or see the `presets` command", MessageType.NEGATIVE))
            return
        if source_string:
            await self.default_channel.send(f"**Acquiring metadata for `{source_string[:64]}`...**")
            async with command.get_channel().typing():
                request = PlaylistRequest(source_string, command.get_author(), use_opus)
                await request.create_metadata(source_string.find(Util.FILE_PROTOCOL_PREFIX) == 0)
                self.playlist.add_queue(request)
                embed = await request.get_embed(MessageType.POSITIVE, pos=len(self.playlist.get_next_queue()))
                await self.default_channel.send(f"**Added to playlist queue:**", embed=embed)
            await self.media_play()


    @commands.command(name='playlist', aliases=['pl'], hidden=False, brief='Show the playlist queue')
    async def command_playlist(self, context: commands.Context):
        command = Command(context.message)
        if not self.is_command_channel(command):
            print(f'{command.get_part(0)} failed check. Aborting.')
            return
        
        embed = await self.playlist.get_embed(command.does_arg_exist('full'), MessageType.INFO)
        await self.default_channel.send(embed=embed)


    @commands.command(name='skip', aliases=['next', 'pass'], hidden=False, brief='Move forward one media track')
    async def command_skip(self, context: commands.Context):
        command = Command(context.message)
        if not self.is_command_channel(command):
            print(f'{command.get_part(0)} failed check. Aborting.')
            return
        
        if Media.user_in_voice_channel(context.author) and self.in_same_voice_channel(context.author) and self.media_manager.get_voice_channel():
            self.playlist.request_movement(PlaylistAction.FORWARD)
            self.media_manager.get_voice_client().stop()


    @commands.command(name='back', aliases=['prev', 'reverse'], hidden=False, brief='Move back one media track')
    async def command_back(self, context: commands.Context):
        command = Command(context.message)
        if not self.is_command_channel(command):
            print(f'{command.get_part(0)} failed check. Aborting.')
            return
        
        if Media.user_in_voice_channel(context.author):
            if self.in_same_voice_channel(context.author):
                if Media.media_manager.get_voice_channel():
                    self.playlist.request_movement(PlaylistAction.BACKWARD)
                    self.media_manager.get_voice_client().stop()


    @commands.command(name='end', aliases=['quit', 'close'], hidden=False, brief='Stops media and clears queue')
    async def command_end(self, context: commands.Context):
        command = Command(context.message)
        if not (self.is_command_channel(command) and self.is_admin_author(command)):
            print(f'{command.get_part(0)} failed check. Aborting.')
            return
        
        if Media.user_in_voice_channel(context.author) and self.in_same_voice_channel(context.author) and Media.media_manager.get_voice_client():
            self.playlist.clear_queue()
            await Media.disconnect_from_voice()


    @commands.command(name='pause', aliases=['halt'], hidden=False, brief='Pauses media, does not leave channel')
    async def command_pause(self, context: commands.Context):
        command = Command(context.message)
        if not self.is_command_channel(command):
            print(f'{command.get_part(0)} failed check. Aborting.')
            return
        
        if Media.user_in_voice_channel(context.author) and self.in_same_voice_channel(context.author) and Media.media_manager.get_voice_client():
            self.media_manager.get_voice_client().pause()


    @commands.command(name='resume', aliases=['continue'], hidden=False, brief='Resumes media, if currently paused')
    async def command_resume(self, context: commands.Context):
        command = Command(context.message)
        if not self.is_command_channel(command):
            print(f'{command.get_part(0)} failed check. Aborting.')
            return
        
        if Media.user_in_voice_channel(context.author) and self.in_same_voice_channel(context.author) and Media.media_manager.get_voice_client():
            self.media_manager.get_voice_client().resume()


    @commands.command(name='clear', hidden=False, brief='Clears the playlist queue')
    async def command_clear(self, context: commands.Context):
        command = Command(context.message)
        if not (self.is_command_channel(command) and self.is_admin_author(command)):
            print(f'{command.get_part(0)} failed check. Aborting.')
            return
        
        clear_all = command.does_arg_exist('all')
        self.playlist.clear_queue(clear_all)
        if clear_all:
            await self.default_channel.send(embed=Util.create_simple_embed("Queue and history have been cleared.", MessageType.INFO))
        else:
            await self.default_channel.send(embed=Util.create_simple_embed("Queue has been cleared.", MessageType.INFO))


    @commands.command(name='presets', aliases=['preset'], hidden=False, brief='Show the list of available media presets')
    async def command_presets(self, context: commands.Context):
        command = Command(context.message)
        if not self.is_command_channel(command):
            print(f'{command.get_part(0)} failed check. Aborting.')
            return
        
        import csv
        preset_list = ""
        try:
            with open(Media.MEDIA_PRESETS_PATH, newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                for i, row in enumerate(reader):
                    # print(row) # [preset, url, desc]
                    if row[0].lower() != 'preset':
                        preset_list = preset_list + f"{i}. `{row[0]}` {row[2]}\n"
            out = f"**The following presets are available when requesting media streams in the format `{Util.get_command_char()}stream --preset=<preset_name>`:**\n{preset_list}"
        except:
            out = "There was a problem reading the presets file."
        await context.send(out)


    # #####################################
    # Media controller
    # #####################################

    async def update_playlist_pointer(self):
        self.media_manager.get_voice_client().stop()
        match self.playlist.get_requested_action():           
            case PlaylistAction.FORWARD:
                self.playlist.iterate_queue()
                await self.default_channel.send(embed=Util.create_simple_embed('Skipping forward one media track.', MessageType.INFO))
            case PlaylistAction.BACKWARD:
                self.playlist.move_back_queue()
                await self.default_channel.send(embed=Util.create_simple_embed('Going back one media track.', MessageType.INFO))
            case PlaylistAction.STAY:
                await self.default_channel.send(embed=Util.create_simple_embed('Track is done. Moving to next one.', MessageType.INFO))
                self.playlist.iterate_queue()
        await self.media_play()


    async def media_play(self):
        if self.playlist.is_end():
            await self.default_channel.send(embed=Util.create_simple_embed("End of playlist. I am leaving. Use `stream` or `search` to request media!", MessageType.INFO))
            await self.disconnect_from_voice()
            return
        
        if self.media_manager.get_voice_client() and self.media_manager.get_voice_client().is_playing():
            print("Media play requested, but audio is active")
            return
        
        # if the playlist has something in it
        request = self.playlist.get_now_playing()
        
        # cancel this media and move to next if the author not known for some reason
        if not request.get_requester():
            await self.default_channel.send(embed=Util.create_simple_embed("Requester is not known. Cannot follow!", MessageType.FATAL))
            self.playlist.iterate_queue()
            return

        # check if the requester is in a voice channel so they can be followed
        target_voice_state = request.get_requester().voice
        if not target_voice_state:
            await self.default_channel.send(embed=Util.create_simple_embed(f'{request.get_requester().name} is not in a voice channel. Going to next playlist item.', MessageType.NEGATIVE))
            self.playlist.iterate_queue()
            return

        # find the voice channel of the requester
        target_voice_channel: discord.channel.VocalGuildChannel = target_voice_state.channel

        # if the bot is not in a channel, join the correct one
        if self.media_manager.get_voice_channel() == None:
            try:
                self.media_manager.set_voice_client(await target_voice_channel.connect())
                self.media_manager.set_voice_channel(target_voice_channel)
            except:
                print("\tUnknown error joining a voice channel")

        # if the bot is already in the target channel, do nothing
        elif self.media_manager.get_voice_channel() == target_voice_channel:
            pass

        # if the bot is in a different channel than the requester, disconnect and switch to the target one
        else:
            await self.media_manager.get_voice_client().disconnect()
            self.media_manager.set_voice_channel(target_voice_channel)
            self.media_manager.set_voice_client(await target_voice_channel.connect())

        # define what to do when the track ends
        def after_media(error):
            print(f'Ended stream for with error: {error}')
            self.media_manager.media_loop.create_task(self.update_playlist_pointer())
        
        # play the stream
        source_string = await request.get_playable_url()
        stream = await self.media_manager.get_stream_from_url(source_string, request.use_opus())
        
        if not stream or not source_string:
            # if something bad really happens, skip this track
            await self.default_channel.send(embed=Util.create_simple_embed('Bad source. Exiting.', MessageType.FATAL))
            self.media_manager.get_voice_client().stop()
            after_media(None)
        else:
            embed = await request.get_embed(MessageType.INFO)
            await self.default_channel.send(f"**Now playing:**", embed=embed)
            self.media_manager.get_voice_client().play(stream, after=after_media)
            await self.buffer_for_seconds(1.0)


    # #####################################
    # Helper Functions
    # #####################################

    async def service_search(self, command: Command):
        service = command.get_part(1).lower()
        keywords = command.get_command_from(2)
        await self.default_channel.send(f"**Conducting search in `{service}` for `{keywords}`. Please wait...**")
        request = None
        async with command.get_channel().typing():
            match service:
                case 'youtube' | 'yt':
                    loop = asyncio.get_event_loop()
                    results =  await loop.run_in_executor(None, lambda: youtube_search.YoutubeSearch(keywords, max_results=1).to_dict())
                    url = f"https://www.youtube.com{results[0]['url_suffix']}"
                    request = PlaylistRequest(url, command.get_author(), command.does_arg_exist('opus'))
                    await request.create_metadata()
                case _:
                    await self.default_channel.send(embed=Util.create_simple_embed(f"Unknown service. Available search providers are `youtube`.", MessageType.NEGATIVE))
            return request


    def in_same_voice_channel(self, user: discord.Member | discord.User) -> bool:
        if not user.voice:
            return False
        else:
            return self.media_manager.get_voice_channel() == user.voice.channel
        

    def user_in_voice_channel(user: discord.Member | discord.User) -> bool:
        if not user.voice:
            return False
        else:
            if user.voice.channel:
                return True
            else:
                return False


    async def disconnect_from_voice(self):
        if self.media_manager.get_voice_client():
            if self.media_manager.get_voice_client().is_playing():
                self.media_manager.get_voice_client().stop()
            await self.media_manager.get_voice_client().disconnect()
        self.media_manager.set_voice_channel(None)


    async def buffer_for_seconds(self, seconds: float):
        if self.media_manager.get_voice_client() and seconds > 0.0:
            print(f"  Allowing {seconds} second buffer")
            self.media_manager.get_voice_client().pause()
            await asyncio.sleep(seconds)
            self.media_manager.get_voice_client().resume()
            print(f"  Resuming...")