import asyncio
from enum import Enum
import json
import os
import discord
import datetime
from discord.ext import commands
from Bot.Event import Event
from Cogs.Tools import Tools
from Command import Command
from Util import MessageType, Util


class EventType(Enum):
    EarthquakePacific = 'eqp'
    EarthquakeGlobal = 'eqg'
    Connection = 'con'
    EventUnknown = '__unknown__'


class Events(commands.Cog):
    EVENT_SUB_PATH = r'Bot/events.json'
    EVENT_POLL_RATE = 5*60 # seconds
    bot: discord.Bot
    lock: asyncio.Lock

    def __init__(self, bot):
        self.bot = bot
        self.lock = asyncio.Lock()

    @commands.Cog.listener()
    async def on_ready(self):
        # list of subscription functions
        # self.bot.dispatch('earthquake_global_watcher')
        # self.bot.dispatch('earthquake_pacific_watcher')
        self.bot.dispatch('event_scanner')
        print(f"READY! Initialized Events cog.")


    # #####################################
    # Manual Checks (does not use built-in cog command checks)
    # #####################################

    def is_command_channel(self, context: commands.Context):
        return isinstance(context.channel, discord.channel.DMChannel) or context.channel.id == Util.DEFAULT_COMMAND_CHANNEL[context.guild.id]
    

    def is_dm(self, context: commands.Context):
        return isinstance(context.channel, discord.channel.DMChannel)


    # #####################################
    # Commands
    # #####################################

    @commands.command(name='event', hidden=False, 
        brief='Subscribe or unsubscribe the channel from an event tracker',
        usage='[sub|unsub] [eqp|eqg|con] OR help',
        description='Subscribe or unsubscribe the channel from an event tracker')
    async def command_event(self, context: commands.Context):
        command = Command(context.message)

        user_id = 0
        channel_id = 0
        if self.is_dm(context):
            user_id = context.author.id
        elif not context.channel.permissions_for(context.author).manage_channels:
            print(f'{command.get_part(0)} failed check. Aborting.')
            return
        
        if not self.is_dm(context):
            channel_id = command.get_channel().id
        action_string = command.get_part(1)
        input_event_string = command.get_part(2)
        param_string = command.get_command_from(3)
        event_status = True
        event_type = EventType.EventUnknown.value
        
        if input_event_string in [EventType.EarthquakeGlobal.value, EventType.EarthquakePacific.value, EventType.Connection.value]:
            event_type = input_event_string

        if not action_string in ['sub', 'unsub'] or event_type == EventType.EventUnknown.value:
            print('Not a valid action')
            return
        
        # find the file to append this channel id to
        file_path = Events.EVENT_SUB_PATH
        
        if not os.path.isfile(file_path):
            await command.get_channel().send(embed=Util.create_simple_embed(f'The event file does not exist. Contact an admin. This should not happen.', MessageType.FATAL))
            return
        
        event_list = await self.load_subscriber_file(file_path)
        if event_list == None:
            await command.get_channel().send(embed=Util.create_simple_embed(f'Error reading event file.', MessageType.FATAL))
            return
        
        new_event_list: list[dict] = []
        event_index = -1
        for i, raw_event in enumerate(event_list):
            event = Event(raw_event['last_checked'], raw_event['event'], raw_event['param'], raw_event['channels'], raw_event['users'], raw_event['latest'])
            new_event_list.append(event.get_dict())
            if event.event_name == event_type and param_string == event.param:
                event_index = i

        if event_index == -1:
            channel_list = [] if channel_id == 0 else [channel_id]
            user_list = [] if user_id == 0 else [user_id]
            event = Event(datetime.datetime.now().timestamp(), event_type, param_string, channel_list, user_list, event_status)
            new_event_list.append(event.get_dict())
        else:
            # add or remove the channel id based on the requested action
            not_valid_action = False
            if action_string == 'sub':
                if channel_id > 0:
                    if not channel_id in new_event_list[event_index]['channels']:
                        new_event_list[event_index]['channels'].append(channel_id)
                    else:
                        not_valid_action = True
                if user_id > 0:
                    if not user_id in new_event_list[event_index]['users']:
                        new_event_list[event_index]['users'].append(user_id)
                    else:
                        not_valid_action = True
            elif action_string == 'unsub':
                if channel_id > 0:
                    if channel_id in new_event_list[event_index]['channels']:
                        new_event_list[event_index]['channels'].remove(channel_id)
                    else:
                        not_valid_action = True
                if user_id > 0:
                    if user_id in new_event_list[event_index]['users']:
                        new_event_list[event_index]['users'].remove(user_id)
                    else:
                        not_valid_action = True
            else:
                await command.get_channel().send(embed=Util.create_simple_embed(f'`{action_string}` is not a valid action.'))
                return

            if not_valid_action:
                await command.get_channel().send(embed=Util.create_simple_embed(f'If subscribing, the ID already exists for this event. If unsubscribing, the ID does not exist for this event.', MessageType.NEGATIVE))
                return
            
        # write new, updated file
        for event in new_event_list:
            if len(event['channels']) == 0 and len(event['users']) == 0:
                print(f'Cleaned up event E:`{event["event"]}`, P:`{event["param"]}`')
                new_event_list.remove(event)
        await self.write_subscriber_file(file_path, new_event_list)

        channel_type = context.guild if context.guild else context.channel.type.name
        channel_name = context.channel.name if not isinstance(context.channel, discord.channel.DMChannel) else context.channel.id
        await command.get_channel().send(embed=Util.create_simple_embed(f'Successfully performed {action_string} on {channel_type} channel {channel_name} for `{event_type}`'))
        await Util.write_dev_log(self.bot, f'{channel_name}/{channel_name} did `{action_string}` on `{event_type}`.')


    # #####################################
    # Event Watcher
    # #####################################

    @commands.Cog.listener()
    async def on_event_scanner(self):
        print('Now looping for new events')
        while True:
            file_path = Events.EVENT_SUB_PATH
            event_list = []
            await self.lock.acquire()
            try:
                # create the file if it does not already exist. Otherwise load the list object that is in the file
                if not os.path.isfile(file_path):
                    with open(file_path, 'a+') as file:
                        json.dump(event_list, file)
                else:
                    with open(file_path, 'r') as file:
                        event_list = json.load(file)
            except Exception as e:
                print(f'There was an error processing {file_path} before API call: {e}')
            self.lock.release()

            # iterate through event list, and send results to all recipients
            for i, event in enumerate(event_list):
                now = datetime.datetime.now().timestamp()
                last_checked = event['last_checked']
                text = None
                embeds = []
                match event['event']:
                    case EventType.EarthquakeGlobal.value:
                        print('global')
                        embeds = await Events.get_earthquake_embeds('Global', last_checked, None, None, None, 6.0)
                    case EventType.EarthquakePacific.value:
                        print('pacific')
                        embeds = await Events.get_earthquake_embeds('Pacific', last_checked, 45.44683044, -122.77973641, 2000, 2.5)
                    case EventType.Connection.value:
                        import platform
                        import subprocess
                        print(f'connection {event["param"]}')
                        # Building the command. Ex: "ping -c 1 google.com"
                        command = ['ping', '-n' if platform.system().lower()=='windows' else '-c', '1', event['param']]
                        result = subprocess.call(command, stdout=open(os.devnull, 'wb')) == 0
                        previous_result = event['latest']
                        if result != previous_result:
                            if result == True:
                                embeds.append(Util.create_simple_embed(f'Ping update: `{event["param"]}` is reachable.', MessageType.POSITIVE))
                            else:
                                embeds.append(Util.create_simple_embed(f'Ping update: `{event["param"]}` is **not** reachable.', MessageType.NEGATIVE))
                        event_list[i]['latest'] = result
                    case _:
                        print('default match')
                event_list[i]['last_checked'] = now
                
                # if there are any updates, send them to users
                if text != None or len(embeds) > 0:
                    for id in event['channels']:
                        channel = self.bot.get_channel(id)
                        if text:
                            await channel.send(text)
                        for embed in embeds:
                            await channel.send(embed=embed)
                    for id in event['users']:
                        channel = self.bot.get_user(id).dm_channel
                        if not channel:
                            print(f'Needed to create channel manually {id}')
                            channel = await self.bot.create_dm(self.bot.get_user(id))
                        if text:
                            await channel.send(text)
                        for embed in embeds:
                            await channel.send(embed=embed)
                
            await self.write_subscriber_file(file_path, event_list)
            await asyncio.sleep(10)


    # #################################
    # Earthquake Helpers
    # #################################

    async def get_earthquake_embeds(title: str, start_time: float, latt: float | None, long: float | None, radius: int | None, min_mag: float):
        new_quakes = await Events.get_earthquakes_since_time(start_time, latt, long, radius, min_mag)

        # perform announcements
        embeds = []
        for quake in new_quakes:
            # (location, mag, time, depth, this_latt, this_long)
            embed = discord.Embed(title=f'{title} Earthquake: {quake[0]}', url=f'https://www.google.com/maps/@{quake[4]},{quake[5]},10z', color=MessageType.INFO.value)
            embed.add_field(name='Location', value=quake[0], inline=False)
            embed.add_field(name='Magnitude', value=quake[1], inline=True)
            embed.add_field(name='Time', value=datetime.datetime.utcfromtimestamp(quake[2]/1000).strftime('%m/%d/%Y, %H:%M:%S UTC'), inline=True)
            embed.add_field(name='Depth', value=f'{quake[3]}km', inline=True)
            embed.add_field(name='Coordinates', value=f'{round(quake[4], 4)}, {round(quake[5], 4)}', inline=False)
            embed.set_footer(text=f'Message generated at {datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S UTC")}\nThis channel is subscribed to the `EarthquakesGlobal` event')
            embeds.append(embed)
        return embeds


    async def get_earthquakes_since_time(start_time=0, center_latt=None, center_long=None, radius=None, min_mag=0.0):
        base_query = 'https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson'
        time_format = datetime.datetime.utcfromtimestamp(start_time).strftime('%Y-%m-%dT%H:%M:%S%z') # 2023-05-30T20:22:58+00:00
        time_string = f'&starttime={time_format}' if start_time else ''
        radius_string = f'&maxradiuskm={radius}' if radius else ''
        mag_string = f'&minmagnitude={min_mag}' if min_mag else ''
        coords = ''
        if center_latt and center_long:
            coords = f'&latitude={center_latt}&longitude={center_long}'
        (response, mime, code) = await Util.http_get(f'{base_query}{time_string}{coords}{radius_string}{mag_string}')

        if not Util.is_200(code):
            print(f'USGS query was not successful ({code})')
            return False
        
        all_earthquakes = response.get('features', [])
        results = []
        for quake in all_earthquakes:
            time = quake.get('properties').get('time', 0)
            mag = quake.get('properties').get('mag', 'Unknown Magnitude')
            location = quake.get('properties').get('place', 'Uninhabited Area')
            depth = quake.get('geometry').get('coordinates')[2]
            this_latt = quake.get('geometry').get('coordinates')[1]
            this_long = quake.get('geometry').get('coordinates')[0]
            results.append((location, mag, time, depth, this_latt, this_long))
        return results
    

    # #################################
    # Helper Functions
    # #################################

    async def write_subscriber_file(self, file_path, event_object):
        if os.path.isfile(file_path):
            try:
                await self.lock.acquire()
                with open(file_path, 'w') as file:
                    json.dump(event_object, file, indent=4)
                self.lock.release()
            except Exception as e:
                self.lock.release()
                print(f'There was an error writing to {file_path} after API call: {e}')
                return False
        else:
            return False
        return True


    async def load_subscriber_file(self, file_path):
        return_object = []
        await self.lock.acquire()
        try:
            if not os.path.isfile(file_path):
                with open(file_path, 'a+') as file:
                    json.dump(return_object, file)
            else:
                with open(file_path, 'r') as file:
                    contents = json.load(file)
                    return_object = contents
        except Exception as e:
            self.lock.release()
            print(f'There was an error processing {file_path} before API call: {e}')
            return None
        self.lock.release()
        return return_object
