import os
import discord
from discord import BotIntegration, FFmpegOpusAudio, FFmpegPCMAudio
import asyncio
from dotenv import load_dotenv
from Quote import Quote
from Command import Command
from Util import Util, PlaylistAction
from InstanceManager import InstanceManager
from MediaManager import MediaManager
from LinearPlaylist import LinearPlaylist
from PlaylistRequest import PlaylistRequest

# env and client setup
load_dotenv()
instance_manager = InstanceManager()
intents = discord.Intents.all()
client = discord.Client(intents=intents)
default_channel = None
media_manager: MediaManager = None
playlist = LinearPlaylist(client)

# on startup
@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    global default_channel
    global media_manager
    media_channel = None
    # find default text channels
    for guild in client.guilds:
        print(guild)
        default_channel = guild.system_channel # first backup channel
        for channel in guild.text_channels:
            # print(f"\tChannel: {channel.name}, Type: {channel.type.name}, isDefault: {channel == default_channel}")
            if channel.name in Util.BOT_COMMAND_CHANNEL_NAMES:
                print(f"Found a (likely) bot-specific channel in {channel.name}")
                default_channel = channel # first choice channel
            if channel.name in Util.MEDIA_REQUEST_CHANNEL_NAMES:
                print(f"Found a (likely) media-spam channel in {channel.name}")
                media_channel = channel # first choice channel
            if default_channel == None:
                print("I have not found a default channel yet!")
                if channel.permissions_for(guild.me).send_messages:
                    default_channel = channel # last resort channel
                    print(f"I have found a default channel at {channel.name}")
    if not media_channel:
        print(f"No media channel found, will use default channel for music requests: {default_channel}")
        media_channel = default_channel
    media_manager = MediaManager(media_channel)
    await default_channel.send("I have arrived.")
    client.dispatch("playlist_watcher")

# user commands
@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return
    
    # check if it is a command
    if message.content.startswith(Command.COMMAND_CHAR):
        command = Command(message)
        # await message.channel.send(command) # verbose

        # route command to different things
        if message.channel.name == default_channel.name:
            match command.get_part(0):
                case 'quote':
                    await command_quote(command)
                case "help":
                    await command_help(command)
        elif message.channel.name == media_manager.get_text_channel().name:
            match command.get_part(0):
                case 'stream':
                    await command_stream(command)
                case 'playlist':
                    await command_playlist(command)
                case 'pl':
                    await command_playlist(command)

# manage commands for adding or displaying quotes
async def command_quote(command: Command):

    def check_channel_response(m): # checking if it's the same user and channel
        return m.author == command.get_author() and m.channel == command.get_channel()
    
    add_to_db = False
    quote = Quote()
    # match the verb of the command
    match command.get_part(1):
        case 'add':
            add_to_db = True
            quote = Quote(quote=command.get_arg('quote').replace('"', '').replace("'", ''), 
                        author=command.get_arg('author'), 
                        location=command.get_arg('location'), 
                        time=command.get_arg('time'))
        case 'direct':
            add_to_db = True
            quote = Quote(perform_parse=True, raw=command.get_command_from(2))
        case _:
            await command.get_message().reply(f"Not a valid command. Please consult `>>help`")

    # add to the database if the action calls for it
    if add_to_db:
        if quote.is_bad():
            await command.get_message().reply(f"Submitted quote was malformed. Please consult `>>quote help`")
            return
        await command.get_message().reply(f"**I will add this quote. Is this correct?** (y/n)\n{quote.get_quote_verbose()}")
        try:
            response = await client.wait_for('message', check=check_channel_response, timeout=20.0)
            if response.content.lower().strip() not in Util.AFFIRMATIVE_RESPONSE:
                await command.get_message().reply(f"I do not see an approval. Canceling")
            else:
                # TODO add the quote to the database
                await command.get_message().reply(f"Added it!")
        except TimeoutError:
            await command.get_message().reply(f"No response provided. Not adding to database.")
            return
        
    # send message to channel if there is a quote that came about this message
    if not quote.is_bad():
        await command.get_message().channel.send(f"> {quote}")

async def command_stream(command: Command):
    # acquire the target source from the input string
    source_string = command.get_command_from(1)
    if not source_string:
        await command.get_message().reply(f"No source URL specified")
        return
    
    request = PlaylistRequest(source_string, command.get_author(), command.get_arg('video'))
    playlist.add_queue(request)
    # if not playlist.get_now_playing():
    #     playlist.iterate_queue()
    return

async def command_playlist(command: Command):
    action = command.get_command_from(1)
    match action:
        case 'show':
            await media_manager.get_text_channel().send(playlist)
        case 'add':
            pass # done via >>stream <item>
        case 'skip':
            if media_manager.get_voice_channel():
                playlist.request_movement(PlaylistAction.FORWARD)
                print(f"Intended target:{playlist.get_next_queue()}")
        case 'next':
            if media_manager.get_voice_channel():
                playlist.request_movement(PlaylistAction.FORWARD)
                print(f"Intended target:{playlist.get_next_queue()}")
        case 'back':
            if media_manager.get_voice_channel():
                playlist.request_movement(PlaylistAction.BACKWARD)
            else:
                playlist.move_back_queue()
                playlist.get_now_playing().update_requester(command.get_author())
            print(f"Intended target:{playlist.get_prev_queue()}")
        case 'prev':
            if media_manager.get_voice_channel():
                playlist.request_movement(PlaylistAction.BACKWARD)
            else:
                playlist.move_back_queue()
                playlist.get_now_playing().update_requester(command.get_author())
            print(f"Intended target:{playlist.get_prev_queue()}")
        case 'clear':
            playlist.clear_queue()
        case 'end':
            if media_manager.get_voice_client():
                playlist.clear_queue()
                await disconnect_from_voice()
        case 'pause':
            if media_manager.get_voice_client():
                media_manager.get_voice_client().pause()
        case 'resume':
            if media_manager.get_voice_client():
                media_manager.get_voice_client().resume()
        case _:
            await command.get_channel().send(f"Unknown action `{action}`.")

# standard help command
async def command_help(message: discord.Message):
    await message.reply(f"Go to https://github.com/maxoakes/discord-bot-scoot-a-zoot/blob/main/Commands.md to see available commands.")

@client.event
async def on_media_playlist_update():
    pass

# loop forever
@client.event
async def on_playlist_watcher():
    await media_manager.get_text_channel().send("I am now taking song and media requests.")
    while True:
        if not playlist.is_end():
            request = playlist.get_now_playing()
            print(f"Starting iteration with {request.get_source_string()}")
            # await media_manager.get_text_channel().send(f"Initializing next request: `{request.get_source_string()}`")
            
            if not request.get_requester():
                await media_manager.get_text_channel().send("Requester is not known. Cannot follow!")
                playlist.iterate_queue()
                continue

            # attempt to follow the requestor to a voice channel
            target_voice_state = request.get_requester().voice
            if target_voice_state:
                # find the voice channel
                target_voice_channel: discord.channel.VocalGuildChannel = target_voice_state.channel

                # if the bot is not in a channel, join the correct one
                if media_manager.get_voice_channel() == None:
                    try:
                        media_manager.set_voice_client(await target_voice_channel.connect())
                        media_manager.set_voice_channel(target_voice_channel)
                    except:
                        print("\terror joining a voice channel")
                # if the bot is already in the target channel, do nothing
                elif media_manager.get_voice_channel() == target_voice_channel:
                    pass
                # if the bot is in a different channel, disconnect and switch to the target one
                else:
                    await media_manager.get_voice_client().disconnect()
                    media_manager.set_voice_channel(target_voice_channel)
                    media_manager.set_voice_client(await target_voice_channel.connect())

                def after_media(error):
                    print(f'\tEnded stream for {request.get_requester().guild.name}')
                    if error:
                        print(error)
                    playlist.allow_progress(True)
                
                # play the stream
                source_string = request.get_source_string()
                (source, metadata) = await media_manager.get_best_stream_from_url(source_string)
                await media_manager.get_text_channel().send(f"Now playing `{metadata}`, requested by `{request.get_requester()}`")
                if not source or not source_string:
                    await media_manager.get_text_channel().send('Bad source. Exiting.')
                    media_manager.get_voice_client().stop()
                    await media_manager.get_voice_client().disconnect()
                    return
                media_manager.get_voice_client().play(source, after=after_media)

                # locking mechanism, stream will not iterate until func after_media is run
                while True:
                    await asyncio.sleep(0.5)
                    # if the media track has ended
                    if playlist.can_progress():
                        break
                    if playlist.get_requested_action() != PlaylistAction.STAY:
                        # force a stop to current track if there is a request to change tracks
                        print(f'\tRequest to move {playlist.get_requested_action()}')
                        media_manager.get_voice_client().stop()
                
                # if we get here, the playlist can progress
                print(f"\tNEXT: can_progress:{playlist.can_progress()}, movement:{playlist.get_requested_action()}")
                match playlist.get_requested_action():
                    case PlaylistAction.FORWARD:
                        playlist.iterate_queue()
                    case PlaylistAction.BACKWARD:
                        playlist.move_back_queue()
                    case PlaylistAction.STAY:
                        playlist.iterate_queue()
                    case _:
                        print(f"unknown action {playlist.get_requested_action()}")

                # reset movement for next iteration
                playlist.request_movement(PlaylistAction.STAY)
                playlist.allow_progress(False)
                # if media_manager.get_voice_client().is_playing():
                #     media_manager.get_voice_client().stop()
                print("\tend of this loop")
            else:
                await media_manager.get_text_channel().send(f'{request.get_requester().name} is not in a voice channel. Going to next playlist item')
                playlist.iterate_queue()
        else:
            if media_manager.get_voice_channel():
                await disconnect_from_voice()
        await asyncio.sleep(1)

async def disconnect_from_voice():
    if media_manager.get_voice_client():
        if media_manager.get_voice_client().is_playing():
            media_manager.get_voice_client().stop()
        await media_manager.get_voice_client().disconnect()
    media_manager.set_voice_channel(None)
client.run(os.getenv('TOKEN'))