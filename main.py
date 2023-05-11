import os
import sys
import discord
from discord import BotIntegration, FFmpegOpusAudio, FFmpegPCMAudio
import asyncio
from dotenv import load_dotenv
from Help import Help
from Quote import Quote
from Command import Command
from Util import Util, PlaylistAction
from MediaManager import MediaManager
from LinearPlaylist import LinearPlaylist
from PlaylistRequest import PlaylistRequest

# set up variable storage
load_dotenv()
intents = discord.Intents.all()
client = discord.Client(intents=intents)
media_manager: MediaManager = MediaManager()
playlist: LinearPlaylist = LinearPlaylist(client)

# set in on_ready
this_guild: discord.Guild
default_command_channel: discord.TextChannel = None
default_media_text_channel: discord.TextChannel = None

# on startup
@client.event
async def on_ready():
    global default_command_channel
    global default_media_text_channel
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
            if channel.name in Util.BOT_COMMAND_CHANNEL_NAMES:
                default_command_channel = channel
            if channel.name in Util.MEDIA_REQUEST_CHANNEL_NAMES:
                default_media_text_channel = channel
        
    # if a default command or media channel is not found, attempt to assign a fallback channel that the users can send commands
    if default_command_channel == None:
        print(f"\tNo default channel found for {this_guild.name}, finding default")
        if temp_default_channel.permissions_for(this_guild.me).send_messages:
            default_command_channel = temp_default_channel
            print(f"I have found a default channel at {this_guild.name}/{channel.name}")
    if default_media_text_channel == None:
        print(f"\tNo media channel found for {this_guild.name}, finding default")
        if temp_default_channel.permissions_for(this_guild.me).send_messages:
            default_media_text_channel = temp_default_channel
            print(f"I have found a default channel at {this_guild.name}/{channel.name}")
    if default_command_channel == None:
        print('WARNING, no default command channel is accessible. This bot will not have full functionality.')
    if default_media_text_channel == None:
        print('WARNING, no default media request channel is accessible. This bot will not have full functionality.')

    # send opening message
    await default_command_channel.send("I have arrived.")
    print(f"Initialized for '{this_guild.name}' with command channel='{default_command_channel}' and media channel='{default_media_text_channel}'")
    client.dispatch('playlist_watcher')

# user commands
@client.event
async def on_message(message: discord.Message):
    # ignore the bots own messages
    if message.author == client.user:
        return
    
    # if the message is a command, try to route and parse it
    if message.content.startswith(Command.COMMAND_CHAR):
        command = Command(message)
        # await message.channel.send(command) # verbose
        await perform_route(command)

async def perform_route(command: Command):
    # non-media commands
    if command.get_message().channel == default_command_channel:
        match command.get_part(0):
            # create or get a quote
            case 'quote':
                await parse_quote_request(command)

            # print the list of commands
            case "help":
                await command.get_channel().send(Help.get_help_markdown(command.get_command_from(1)))

            # unknown command
            case _:
                await command.get_message().reply(f"Not a valid command. Please consult `>>help`")

    # media/playlist commands
    elif command.get_message().channel == default_media_text_channel:
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
                        print(command.get_command_from(2))
                        results = youtube_search.YoutubeSearch(command.get_command_from(2), max_results=1).to_dict()
                        url = f"https://www.youtube.com{results[0]['url_suffix']}"
                        request = PlaylistRequest(url, command.get_author(), command.get_arg('video') != None)
                        playlist.add_queue(request)
                    case _:
                        await command.get_channel().send("Unknown service. Consult `>>help search`")

            # add something to the playlist
            case 'add' | 'stream' | 'listen' | 'watch' | 'queue':
                request = await parse_playlist_request(command)
                if request:
                    playlist.add_queue(request)

            # show the current playlist
            case 'playlist' | 'pl' | 'show':
                await default_media_text_channel.send(playlist)

            # skip the current media and go to the next queue item
            case 'next' | 'skip' | 'pass':
                if is_author_in_voice_channel:
                    if is_bot_in_same_voice_channel_as_author:
                        if current_bot_voice_channel:
                            playlist.request_movement(PlaylistAction.FORWARD)
                            print(f"Intended target:{playlist.get_next_queue()}")

            # stop the current media and go to previous item on the queue history
            case 'prev' | 'back' | 'reverse':
                if is_author_in_voice_channel:
                    if is_bot_in_same_voice_channel_as_author:
                        if current_bot_voice_channel:
                            playlist.request_movement(PlaylistAction.BACKWARD)
                        else:
                            playlist.move_back_queue()
                            playlist.get_now_playing().update_requester(command.get_author())
                        print(f"Intended target:{playlist.get_prev_queue()}")

            # clear the playlist queue
            case 'clear':
                clear_all = command.get_arg('all') != None
                playlist.clear_queue(clear_all)
                if clear_all:
                    await command.get_channel().send(f"Queue and history have been cleared.")
                else:
                    await command.get_channel().send(f"Queue has been cleared.")    
                
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
            case "help":
                await command.get_channel().send(Help.get_help_markdown(command.get_command_from(1)))

            # there is an unknown command that a user entered in the media text channel
            case _:
                await command.get_channel().send(f"Unknown action `{command.get_part(0)}`.")

# manage commands for adding or displaying quotes
async def parse_quote_request(command: Command):

    def check_channel_response(m): # checking if it's the same user and channel
        return m.author == command.get_author() and m.channel == command.get_channel()
    
    add_to_db = False
    quote: Quote
    # match the verb of the command
    match command.get_part(1):
        # create a quote carefully using flags
        case 'add':
            add_to_db = True
            quote = Quote(quote=command.get_arg('quote').replace('"', '').replace("'", ''), 
                        author=command.get_arg('author'), 
                        location=command.get_arg('location'), 
                        time=command.get_arg('time'))
            
        # create a quote like one would do if they were writing text
        case 'direct':
            add_to_db = True
            quote = Quote(perform_parse=True, raw=command.get_command_from(2))

        # get a quote from a database
        case 'get':
            # TODO implement SQL select query to local DB
            pass

        # unknown command
        case _:
            await command.get_message().reply(f"Not a valid command. Please consult `>>help`")

    # add to the database if the action calls for it
    if add_to_db:
        if quote.is_bad():
            await command.get_message().reply(f"Submitted quote was malformed. Please consult `>>help`")
            return
        
        # confirm the quote to add, and wait for reply
        await command.get_message().reply(f"**I will add this quote. Is this correct?** (y/n)\n{quote.get_quote_verbose()}")
        try:
            response = await client.wait_for('message', check=check_channel_response, timeout=20.0)
            # check if there is an affirmative response from the same person
            if response.content.lower().strip() in Util.AFFIRMATIVE_RESPONSE and command.get_author().id == response.author.id:
                # TODO implement insert query to local DB
                await command.get_message().reply(f"Added it!")
            else:
                await command.get_message().reply(f"I do not see an approval. Canceling.")
        except TimeoutError:
            await command.get_message().reply(f"No response provided. Not adding to database.")
            return
        
    # send message to channel if there is a quote that came about this message
    if not quote.is_bad():
        await command.get_message().channel.send(f"> {quote}")

async def parse_playlist_request(command: Command):
    # acquire the target source from the input string
    source_string = command.get_command_from(1).strip()

    # check if the request is for a video with flag '--video'
    vid = command.get_arg('video') != None

    # check if there is a preset quest
    preset = command.get_arg('preset')
    if preset:
        # if there is a preset request, try to find that preset
        import csv
        try:
            with open('presets.csv', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    # print(row) # [preset, url, is_vid]
                    if row[0].lower() == preset.lower():
                        source_string = row[1]
                        vid = row[2].lower() in Util.AFFIRMATIVE_RESPONSE
        except Exception as e:
            await command.get_message().reply(f"An error occurred reading your request. Nothing will be added to the queue.")
            print(e)

    # if there was no source url or valid preset, it is a bad request
    if source_string == "":
        await command.get_message().reply(f"Bad source given. Nothing will be added to the queue.")
        return None
    else:
        return PlaylistRequest(source_string, command.get_author(), vid)

# loop forever
@client.event
async def on_playlist_watcher():
    await default_media_text_channel.send("I am now taking song and media requests.")
    while True:
        # if there is something in the playlist queue, attempt to play it
        if not playlist.is_end():
            request = playlist.get_now_playing()
            print(f"Starting iteration with {request.get_source_string()}")
            # await default_media_text_channel.send(f"Initializing next request: `{request.get_source_string()}`")
            
            # cancel this media and move to next if the author not known for some reason
            if not request.get_requester():
                await default_media_text_channel.send("Requester is not known. Cannot follow!")
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

                # if the bot is in a different channel than the requester, disconnect and switch to the target one
                else:
                    await media_manager.get_voice_client().disconnect()
                    media_manager.set_voice_channel(target_voice_channel)
                    media_manager.set_voice_client(await target_voice_channel.connect())

                # define what to do when the track ends
                def after_media(error):
                    print(f'\tEnded stream for {request.get_requester().guild.name}')
                    if error:
                        print(error)
                    # toggle switch to progress to next track
                    playlist.allow_progress(True)
                
                # play the stream
                source_string = request.get_source_string()
                (source, metadata) = await media_manager.get_best_stream_from_url(source_string)
                await default_media_text_channel.send(f"Now playing `{metadata}`, requested by `{request.get_requester()}`")
                if not source or not source_string:
                    # if something bad really happens, skip this track
                    await default_media_text_channel.send('Bad source. Exiting.')
                    media_manager.get_voice_client().stop()
                    await media_manager.get_voice_client().disconnect()
                    playlist.allow_progress(True)
                else:
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
                        print(f"unknown action `{playlist.get_requested_action()}`")

                # reset movement for next iteration
                playlist.request_movement(PlaylistAction.STAY)
                playlist.allow_progress(False)
            else:
                await default_media_text_channel.send(f'{request.get_requester().name} is not in a voice channel. Going to next playlist item')
                playlist.iterate_queue()
            print("\tEnd of media playlist loop")
        else:
            # playlist has nothing on it or at its end. Retract the bot and do nothing
            if media_manager.get_voice_channel():
                await disconnect_from_voice()
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

client.run(os.getenv('TOKEN'))