import os
import sys
import discord
import asyncio
from dotenv import load_dotenv
from Help import Help
from Command import Command
from Util import MessageType, Util
from Media.MediaManager import MediaManager
from Media.LinearPlaylist import LinearPlaylist, PlaylistAction
from Media.PlaylistRequest import PlaylistRequest

# set up variable storage
load_dotenv()
intents = discord.Intents.all()
client = discord.Client(intents=intents)
media_manager: MediaManager = MediaManager()
playlist: LinearPlaylist = LinearPlaylist(client)

# set in on_ready
this_guild: discord.Guild
default_channel: discord.TextChannel = None

# on startup
@client.event
async def on_ready():
    global default_channel
    global this_guild

    # select the server to manage
    print("Available Guilds:")
    for i, g in enumerate(client.guilds):
        print(f"  [{i}] = {g.name} ({g.id})")
    
    try:
        selected_guild: int
        if len(sys.argv) > 1:
            selected_guild = int(sys.argv[1])
        else:
            selected_guild = input("Index Number Guild to manage: ")
        this_guild = client.guilds[int(selected_guild)]
    except:
        print("ERROR, Could not properly parse input. Selecting first entry...")
        this_guild = client.guilds[0]

    print(f"We have logged in as {client.user} and am now managing '{this_guild.name}' ({this_guild.id}).")

    # attempt to find the default channel
    temp_default_channel = this_guild.system_channel

    # attempt to find the two types of channels for the purpose of this bot
    for channel in this_guild.text_channels:
        if channel.permissions_for(this_guild.me).send_messages:
            if channel.name in Util.MEDIA_REQUEST_CHANNEL_NAMES:
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
    client.dispatch('playlist_watcher')

# user commands
@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return
    
    if not message.content.startswith(Command.COMMAND_CHAR):
        return
    
    if message.channel.id != default_channel.id:
        return
    
    command = Command(message)
    await perform_route(command)

async def perform_route(command: Command):
    is_author_in_voice_channel = user_in_voice_channel(command.get_author())
    is_bot_in_same_voice_channel_as_author = in_same_voice_channel(command.get_author())
    current_bot_voice_channel = media_manager.get_voice_channel()
    current_bot_voice_client = media_manager.get_voice_client()

    match command.get_part(0):
        # lookup AND add to queue from a service
        case 'search' | 'lookup' | 'query':
            match command.get_part(1).lower():
                case 'youtube' | 'yt':
                    import youtube_search
                    results = youtube_search.YoutubeSearch(command.get_command_from(2), max_results=1).to_dict()
                    url = f"https://www.youtube.com{results[0]['url_suffix']}"
                    request = PlaylistRequest(url, command.get_author(), command.does_arg_exist('opus'))
                    playlist.add_queue(request)
                    await default_channel.send(f"**Added to playlist queue**", embed=request.get_embed(MessageType.POSITIVE, pos=len(playlist.get_next_queue())))
                case _:
                    await default_channel.send(embed=Util.create_simple_embed(f"Unknown service. Consult `>>help search`", MessageType.NEGATIVE))

        # add media from specific URL to the playlist
        case 'add' | 'stream' | 'listen' | 'queue':
            (source, use_opus) = await parse_playlist_request(command)
            if source.find('http') == -1 and source.find('file') == -1:
                await default_channel.send(embed=Util.create_simple_embed(f"Bad source URI. Must be an `http://`, `https://` or `file://` protocol", MessageType.NEGATIVE))
                return
            
            if source:
                request = PlaylistRequest(source, command.get_author(), use_opus)
                playlist.add_queue(request)
                await default_channel.send(f"**Added to playlist queue**", embed=request.get_embed(MessageType.POSITIVE, pos=len(playlist.get_next_queue())))

        # show the current playlist
        case 'playlist' | 'pl' | 'show':
            await default_channel.send(embed=playlist.get_embed(command.does_arg_exist('full'), MessageType.INFO))

        # skip the current media and go to the next queue item
        case 'next' | 'skip' | 'pass':
            if is_author_in_voice_channel:
                if is_bot_in_same_voice_channel_as_author:
                    if current_bot_voice_channel:
                        playlist.request_movement(PlaylistAction.FORWARD)

        # stop the current media and go to previous item on the queue history
        case 'prev' | 'back' | 'reverse':
            if is_author_in_voice_channel:
                if is_bot_in_same_voice_channel_as_author:
                    if current_bot_voice_channel:
                        playlist.request_movement(PlaylistAction.BACKWARD)
                    else:
                        playlist.move_back_queue()
                        playlist.get_now_playing().update_requester(command.get_author())

        # clear the playlist queue
        case 'clear':
            clear_all = command.does_arg_exist('all')
            playlist.clear_queue(clear_all)
            if clear_all:
                await default_channel.send(embed=Util.create_simple_embed("Queue and history have been cleared.", MessageType.INFO))
            else:
                await default_channel.send(embed=Util.create_simple_embed("Queue has been cleared.", MessageType.INFO))
            
        # clear the queue, stop playing, and return the voice bot
        case 'end':
            if is_author_in_voice_channel:
                if is_bot_in_same_voice_channel_as_author:
                    if current_bot_voice_client:
                        playlist.clear_queue()
                        await disconnect_from_voice()

        # pause playing and maintain the bot in the current channel
        case 'pause':
            if is_author_in_voice_channel:
                if is_bot_in_same_voice_channel_as_author:
                    if current_bot_voice_client:
                        current_bot_voice_client.pause()
        
        # resume playing in the bot's current channel
        case 'resume':
            if is_author_in_voice_channel:
                if is_bot_in_same_voice_channel_as_author:
                    if current_bot_voice_client:
                        current_bot_voice_client.resume()

        # print the list of commands
        case 'help':
            await command.get_channel().send(Help.get_dj_help_markdown(command.get_command_from(1)))

        # there is an unknown command that a user entered in the media text channel
        case _:
            await command.get_channel().send(embed=Util.create_simple_embed(f"Unknown action `{command.get_part(0)}`.", MessageType.NEGATIVE))

async def parse_playlist_request(command: Command):
    # acquire the target source from the input string
    source_string = command.get_command_from(1).strip()
    use_opus = command.does_arg_exist('opus')

    # check if there is a preset quest
    preset = command.get_arg('preset')
    if preset:
        # if there is a preset request, try to find that preset
        import csv
        try:
            with open(r'DJ/presets.csv', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    # print(row) # [preset, url, desc, use_opus]
                    if row[0].lower() == preset.lower():
                        source_string = row[1]
                        use_opus = row[3].lower() in Util.AFFIRMATIVE_RESPONSE
        except Exception as e:
            await command.get_message().channel.send(
                f"How did this happen, {os.getenv('AUTHOR_MENTION')}?", 
                embed=Util.create_simple_embed("An error occurred getting a the media presets, nothing will be added to the queue.", MessageType.FATAL))
            print(e)

    # if there was no source url or valid preset, it is a bad request
    if source_string == "":
        await command.get_message().channel.send(embed=Util.create_simple_embed(f"Bad source was provided. Nothing will be added to the queue.", MessageType.NEGATIVE))
        return (None, False)
    else:
        return (source_string, use_opus)

# loop forever
@client.event
async def on_playlist_watcher():
    await default_channel.send("**I am now taking song and media requests.**")
    while True:
        # check if playlist has anything in the queue
        if playlist.is_end():
            if media_manager.get_voice_channel():
                await default_channel.send(embed=Util.create_simple_embed('Playlist queue is empty. I am leaving.', MessageType.INFO))
                await disconnect_from_voice()
            await asyncio.sleep(0.5)
            continue

        # if the playlist has something in it
        request = playlist.get_now_playing()
        print(f"Starting iteration with {request.get_source_string()}")
        
        # cancel this media and move to next if the author not known for some reason
        if not request.get_requester():
            await default_channel.send(embed=Util.create_simple_embed("Requester is not known. Cannot follow!", MessageType.FATAL))
            playlist.iterate_queue()
            continue

        # check if the requester is in a voice channel so they can be followed
        target_voice_state = request.get_requester().voice
        if not target_voice_state:
            await default_channel.send(embed=Util.create_simple_embed(f'{request.get_requester().name} is not in a voice channel. Going to next playlist item.', MessageType.NEGATIVE))
            playlist.iterate_queue()
            continue

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
            playlist.allow_progress(True) # toggle switch to progress to next track
        
        # play the stream
        source_string = request.get_source_string()
        stream = await media_manager.get_stream_from_url(source_string, request.use_opus())
        await default_channel.send(f"**Now playing:**", embed=request.get_embed(MessageType.INFO))
        
        if not stream or not source_string:
            # if something bad really happens, skip this track
            await default_channel.send(embed=Util.create_simple_embed('Bad source. Exiting.', MessageType.FATAL))
            media_manager.get_voice_client().stop()
            await media_manager.get_voice_client().disconnect()
            playlist.allow_progress(True)
        else:
            media_manager.get_voice_client().play(stream, after=after_media)

        # locking mechanism, stream will not iterate until func after_media is run
        while True:
            await asyncio.sleep(0.5)
            # if the media track has ended
            if playlist.can_progress():
                break
            if playlist.get_requested_action() != PlaylistAction.STAY:
                # happens when a user requests to skip or move back one track
                print(f'\tRequest to move {playlist.get_requested_action()}')
                media_manager.get_voice_client().stop() # triggers after_media to run
        
        # if we get here, the playlist can progress
        print(f"\tNEXT: can_progress:{playlist.can_progress()}, movement:{playlist.get_requested_action()}")
        match playlist.get_requested_action():
            case PlaylistAction.FORWARD:
                playlist.iterate_queue()
                await default_channel.send(embed=Util.create_simple_embed('Skipping forward one media track.', MessageType.INFO))
            case PlaylistAction.BACKWARD:
                playlist.move_back_queue()
                await default_channel.send(embed=Util.create_simple_embed('Going back one media track.', MessageType.INFO))
            case PlaylistAction.STAY:
                playlist.iterate_queue()
                await default_channel.send(embed=Util.create_simple_embed('Track is done. Moving to next one.', MessageType.INFO))
            case _:
                playlist.iterate_queue()
                print(f"unknown action `{playlist.get_requested_action()}`")

        # reset movement for next iteration
        playlist.request_movement(PlaylistAction.STAY)
        playlist.allow_progress(False)
        print("\tEnd of media playlist loop")
        await asyncio.sleep(1)

# #################
# Helper Functions
# #################

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

client.run(os.getenv('DJ_TOKEN'))