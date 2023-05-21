import os
import sys
import discord
from discord.ext import commands
import asyncio
import youtube_search
from dotenv import load_dotenv
from Command import Command
from Util import MessageType, Util
from Media.MediaManager import MediaManager
from Media.LinearPlaylist import LinearPlaylist, PlaylistAction
from Media.PlaylistRequest import PlaylistRequest

MEDIA_PRESETS_PATH = r'Media/presets.csv'
load_dotenv()
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=Command.COMMAND_CHAR, intents=intents)
media_manager: MediaManager = MediaManager()
playlist: LinearPlaylist = LinearPlaylist(bot)
this_guild: discord.Guild
default_channel: discord.TextChannel = None

# on startup
@bot.event
async def on_ready():
    global default_channel
    global this_guild

    # select the server to manage
    print("Available Guilds:")
    for i, g in enumerate(bot.guilds):
        print(f"  [{i}] = {g.name} ({g.id})")
    
    try:
        selected_guild: int
        if len(sys.argv) > 1:
            selected_guild = int(sys.argv[1])
        else:
            selected_guild = input("Index Number Guild to manage: ")
        this_guild = bot.guilds[int(selected_guild)]
    except:
        print("ERROR, Could not properly parse input. Selecting first entry...")
        this_guild = bot.guilds[0]

    print(f"We have logged in as {bot.user} and am now managing '{this_guild.name}' ({this_guild.id}).")

    # attempt to find the default channel
    temp_default_channel = this_guild.system_channel

    # attempt to find the two types of channels for the purpose of this bot
    for channel in this_guild.text_channels:
        if channel.permissions_for(this_guild.me).send_messages:
            if channel.name in ['jukebox', 'music-requests', 'dj-requests']:
                default_channel = channel
        
    # if media channel is not found, attempt to assign a fallback channel that the users can send commands
    if default_channel == None:
        print(f"\tNo media channel found for {this_guild.name}, finding default")
        if temp_default_channel.permissions_for(this_guild.me).send_messages:
            default_channel = temp_default_channel
            print(f"I have found a default channel at {this_guild.name}/{channel.name}")
    if default_channel == None:
        print('WARNING, no default media request channel is accessible. This bot will not have full functionality.')

    # send opening message
    print(f"Initialized for '{this_guild.name}' with default-channel='{default_channel}'")
    # bot.dispatch('media_player')


# #####################################
# Commands
# #####################################

@bot.command(name='work', hidden=True)
async def command_work(context: commands.Context, arg=200):
    await context.channel.send(f"Working...")
    q = 2
    for i in range(int(arg)):
        q = pow(q, q) % 500000
        await asyncio.sleep(0.1)
        print((i))
    await context.channel.send(f"Done working {i}")


@bot.command(name='ping', aliases=['pp'], hidden=True, brief='Get a response')
async def command_ping(context: commands.Context):
    await context.reply('pong')


@bot.command(name='search', aliases=['lookup', 'query'], hidden=False, brief='Search a service for some media')
async def command_search(context: commands.Context):
    command = Command(context.message)
    request = await service_search(command)
    if request:
        await default_channel.send(f"**Adding this search result to playlist queue:**", embed=request.get_embed(MessageType.POSITIVE, pos=len(playlist.get_next_queue())))
        playlist.add_queue(request)
        await media_play()


@bot.command(name='stream', aliases=['add', 'listen', 'queue'], hidden=False, brief='Add a specific URL to the playlist queue')
async def command_stream(context: commands.Context):
    command = Command(context.message)
    source_string = command.get_command_from(1).strip()
    use_opus = command.does_arg_exist('opus')
    preset = command.get_arg('preset')
    if preset:
        # if there is a preset, get it from the presets file
        import csv
        try:
            with open(MEDIA_PRESETS_PATH, newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    # [preset, url, desc, use_opus]
                    if row[0].lower() == preset.lower():
                        source_string = row[1]
                        use_opus = row[3].lower() in Util.AFFIRMATIVE_RESPONSE
        except Exception as e:
            await command.get_message().channel.send(
                f"How did this happen, {os.getenv('AUTHOR_MENTION')}?", 
                embed=Util.create_simple_embed("An error occurred getting a the media presets, nothing will be added to the queue.", MessageType.FATAL))
            print(f'Error processing presets file: {e}')
    # if there was no source url or valid preset, it is a bad request
    if source_string == "" or (source_string.find('http') != 0 and source_string.find('file') != 0):
        await default_channel.send(embed=Util.create_simple_embed(f"Bad source URI. Must be an `http://`, `https://` or `file://` protocol", MessageType.NEGATIVE))
        return
    if source_string:
        request = PlaylistRequest(source_string, command.get_author(), use_opus)
        await request.create_metadata(source_string.find(Util.FILE_PROTOCOL_PREFIX) == 0)
        playlist.add_queue(request)
        await default_channel.send(f"**Added to playlist queue:**", embed=request.get_embed(MessageType.POSITIVE, pos=len(playlist.get_next_queue())))
        await media_play()


@bot.command(name='playlist', aliases=['pl'], hidden=False, brief='Show the playlist queue')
async def command_playlist(context: commands.Context):
    command = Command(context.message)
    await default_channel.send(embed=playlist.get_embed(command.does_arg_exist('full'), MessageType.INFO))


@bot.command(name='skip', aliases=['next', 'pass'], hidden=False, brief='Move forward one media track')
async def command_skip(context: commands.Context):
    if user_in_voice_channel(context.author) and in_same_voice_channel(context.author) and media_manager.get_voice_channel():
        playlist.request_movement(PlaylistAction.FORWARD)
        media_manager.get_voice_client().stop()


@bot.command(name='back', aliases=['prev', 'reverse'], hidden=False, brief='Move back one media track')
async def command_back(context: commands.Context):
    if user_in_voice_channel(context.author):
        if in_same_voice_channel(context.author):
            if media_manager.get_voice_channel():
                playlist.request_movement(PlaylistAction.BACKWARD)
                media_manager.get_voice_client().stop()


@bot.command(name='end', aliases=['quit', 'close'], hidden=False, brief='Stops media and clears queue')
async def command_end(context: commands.Context):
    if user_in_voice_channel(context.author) and in_same_voice_channel(context.author) and media_manager.get_voice_client():
        playlist.clear_queue()
        await disconnect_from_voice()


@bot.command(name='pause', aliases=['halt'], hidden=False, brief='Pauses media, does not leave channel')
async def command_pause(context: commands.Context):
    if user_in_voice_channel(context.author) and in_same_voice_channel(context.author) and media_manager.get_voice_client():
        media_manager.get_voice_client().pause()


@bot.command(name='resume', aliases=['continue'], hidden=False, brief='Resumes media, if currently paused')
async def command_resume(context: commands.Context):
    if user_in_voice_channel(context.author) and in_same_voice_channel(context.author) and media_manager.get_voice_client():
        media_manager.get_voice_client().resume()


@bot.command(name='clear', hidden=False, brief='Clears the playlist queue')
async def command_clear(context: commands.Context):
    command = Command(context.message)
    clear_all = command.does_arg_exist('all')
    playlist.clear_queue(clear_all)
    if clear_all:
        await default_channel.send(embed=Util.create_simple_embed("Queue and history have been cleared.", MessageType.INFO))
    else:
        await default_channel.send(embed=Util.create_simple_embed("Queue has been cleared.", MessageType.INFO))


@bot.command(name='presets', aliases=['preset'], hidden=False, brief='Show the list of available media presets')
async def command_presets(context: commands.Context):
    import csv
    preset_list = ""
    try:
        with open(MEDIA_PRESETS_PATH, newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            for i, row in enumerate(reader):
                # print(row) # [preset, url, desc]
                if row[0].lower() != 'preset':
                    preset_list = preset_list + f"\n {i}. `{row[0]}` {row[2]}"
        out = f"**The following presets are available when requesting media streams in the format `>>stream --preset=<preset_name>`:**\n{preset_list}"
    except:
        out = "There was a problem reading the presets file."
    await context.send(out)


# #####################################
# Media controller
# #####################################

async def update_playlist_pointer():
    media_manager.get_voice_client().stop()
    match playlist.get_requested_action():           
        case PlaylistAction.FORWARD:
            playlist.iterate_queue()
            await default_channel.send(embed=Util.create_simple_embed('Skipping forward one media track.', MessageType.INFO))
        case PlaylistAction.BACKWARD:
            playlist.move_back_queue()
            await default_channel.send(embed=Util.create_simple_embed('Going back one media track.', MessageType.INFO))
        case PlaylistAction.STAY:
            await default_channel.send(embed=Util.create_simple_embed('Track is done. Moving to next one.', MessageType.INFO))
            playlist.iterate_queue()
    await media_play()


async def media_play():
    if playlist.is_end():
        await default_channel.send(embed=Util.create_simple_embed("End of playlist. I am leaving. Use `stream` or `search` to request media!", MessageType.INFO))
        await disconnect_from_voice()
        return
    
    if media_manager.get_voice_client() and media_manager.get_voice_client().is_playing():
        print("Media play requested, but audio is active")
        return
    
    # if the playlist has something in it
    request = playlist.get_now_playing()
    
    # cancel this media and move to next if the author not known for some reason
    if not request.get_requester():
        await default_channel.send(embed=Util.create_simple_embed("Requester is not known. Cannot follow!", MessageType.FATAL))
        playlist.iterate_queue()
        return

    # check if the requester is in a voice channel so they can be followed
    target_voice_state = request.get_requester().voice
    if not target_voice_state:
        await default_channel.send(embed=Util.create_simple_embed(f'{request.get_requester().name} is not in a voice channel. Going to next playlist item.', MessageType.NEGATIVE))
        playlist.iterate_queue()
        return

    # find the voice channel of the requester
    target_voice_channel: discord.channel.VocalGuildChannel = target_voice_state.channel

    # if the bot is not in a channel, join the correct one
    if media_manager.get_voice_channel() == None:
        try:
            media_manager.set_voice_client(await target_voice_channel.connect())
            media_manager.set_voice_channel(target_voice_channel)
        except:
            print("\tUnknown error joining a voice channel")

    # if the bot is already in the target channel, do nothing
    elif media_manager.get_voice_channel() == target_voice_channel:
        pass

    # if the bot is in a different channel than the requester, disconnect and switch to the target one
    else:
        await media_manager.get_voice_client().disconnect()
        media_manager.set_voice_channel(target_voice_channel)
        media_manager.set_voice_client(await target_voice_channel.connect())

    # define what to do when the track ends
    def after_media(error):
        print(f'\tEnded stream for {request.get_requester().guild.name} with error: {error}')
        media_manager.media_loop.create_task(update_playlist_pointer())
    
    # play the stream
    source_string = request.get_playable_url()
    stream = await media_manager.get_stream_from_url(source_string, request.use_opus())
    
    if not stream or not source_string:
        # if something bad really happens, skip this track
        await default_channel.send(embed=Util.create_simple_embed('Bad source. Exiting.', MessageType.FATAL))
        media_manager.get_voice_client().stop()
        after_media(None)
    else:
        await default_channel.send(f"**Now playing:**", embed=request.get_embed(MessageType.INFO))
        media_manager.get_voice_client().play(stream, after=after_media)


# #####################################
# Helper Functions
# #####################################

async def service_search(command: Command):
    service = command.get_part(1).lower()
    keywords = command.get_command_from(2)
    await default_channel.send(f"**Conducting search in `{service}` for `{keywords}`. Please wait...**")
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
                await default_channel.send(embed=Util.create_simple_embed(f"Unknown service. Available search providers are `youtube`.", MessageType.NEGATIVE))
        return request


def in_same_voice_channel(user: discord.Member | discord.User) -> bool:
    if not user.voice:
        return False
    else:
        return media_manager.get_voice_channel() == user.voice.channel
    

def user_in_voice_channel(user: discord.Member | discord.User) -> bool:
    if not user.voice:
        return False
    else:
        if user.voice.channel:
            return True
        else:
            return False


async def disconnect_from_voice():
    if media_manager.get_voice_client():
        if media_manager.get_voice_client().is_playing():
            media_manager.get_voice_client().stop()
        await media_manager.get_voice_client().disconnect()
    media_manager.set_voice_channel(None)


bot.run(os.getenv('DJ_TOKEN'))