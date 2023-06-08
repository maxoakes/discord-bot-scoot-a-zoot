import asyncio
from enum import Enum
import json
import os
import discord
import datetime
from discord.ext import commands
from Cogs.Tools import Tools
from Command import Command
from Util import MessageType, Util


class EventType(Enum):
    EarthquakePacific = 'earthquake_pacific'
    EarthquakeGlobal = 'earthquake_global'
    EventUnknown = '__unknown__'


class Events(commands.Cog):
    EVENT_SUB_PATH = r'EventSubscribers/'
    EVENT_POLL_RATE = 5*60 # seconds
    bot: discord.Bot

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        # list of subscription functions
        self.bot.dispatch('earthquake_global_watcher')
        self.bot.dispatch('earthquake_pacific_watcher')
        print(f"READY! Initialized Events cog.")


    # #####################################
    # Manual Checks (does not use built-in cog command checks)
    # #####################################

    def is_command_channel(self, context: commands.Context):
        return isinstance(context.channel, discord.channel.DMChannel) or context.channel.id == Util.DEFAULT_COMMAND_CHANNEL[context.guild.id]


    # #####################################
    # Commands
    # #####################################

    @commands.command(name='event', hidden=False, 
        brief='Subscribe or unsubscribe the channel from an event tracker',
        usage='<[sub|unsub] [earthquakes_pacific|earthquakes_global]>',
        description='Subscribe or unsubscribe the channel from an event tracker')
    async def command_event(self, context: commands.Context):
        command = Command(context.message)
        if not context.channel.permissions_for(context.author).manage_channels:
            print(f'{command.get_part(0)} failed check. Aborting.')
            return
        
        input_event_string = command.get_part(2)
        event_type = EventType.EventUnknown

        if input_event_string == 'earthquakes_pacific':
            event_type = EventType.EarthquakePacific
            
        elif input_event_string == 'earthquakes_global':
            event_type = EventType.EarthquakeGlobal

        # final check before performing the action
        action_string = command.get_part(1)
        if not action_string in ['sub', 'unsub'] or event_type == EventType.EventUnknown:
            return
        
        # find the file to append this channel id to
        file_path = fr'{Events.EVENT_SUB_PATH}{event_type.value}.json'
        channel_to_add = command.get_channel().id

        if os.path.isfile(file_path):
            try:
                # attempt to get file contents
                contents = {}
                with open(file_path, 'r') as file:
                    file_contents: dict[int, list[int]] = json.load(file)
                    contents = file_contents

                # add or remove the channel id based on the requested action
                if action_string == 'sub':
                    if not channel_to_add in contents['subscribers']:
                        contents['subscribers'].append(channel_to_add)
                    else:
                        await command.get_channel().send(embed=Util.create_simple_embed(f'This channel is already subscribed to this event'))
                        return
                else:
                    contents['subscribers'].remove(channel_to_add)

                # write the object back to the file
                with open(file_path, 'w') as file:
                    json.dump(contents, file)

                channel_string = command.get_channel()
                await command.get_channel().send(embed=Util.create_simple_embed(f'Successfully performed {action_string} on channel {channel_string} for {event_type.value}'))
                await Util.write_dev_log(self.bot, f'{command.get_guild()}/{channel_string} did `{action_string}` on {event_type.value}.')

            except ValueError as v:
                print(f'No such channel is subscribed to that event: {v}')
            except Exception as e:
                print(f'There was an error subscribing {channel_to_add} to {file_path}: {e}')


    # #####################################
    # Subscription Events
    # #####################################

    @commands.Cog.listener()
    async def on_earthquake_global_watcher(self):
        print('now watching for new global earthquake events')
        file_path = fr'{Events.EVENT_SUB_PATH}{EventType.EarthquakeGlobal.value}.json'
        await Events.generic_earthquake_watcher('Global', file_path, None, None, None, 6.0)


    @commands.Cog.listener()
    async def on_earthquake_pacific_watcher(self):
        print('now watching for new pacific earthquake events')
        file_path = fr'{Events.EVENT_SUB_PATH}{EventType.EarthquakePacific.value}.json'
        await Events.generic_earthquake_watcher('Pacific', file_path, 45.44683044, -122.77973641, 200, 3.5)


    async def generic_earthquake_watcher(earthquake_display_string, file_path, latt, long, radius, min_mag):
        while True:
            # define the basic contents of the subscriber file, in case there is no file and it needs to be written this loop
            now = datetime.datetime.now().timestamp()
            this_iteration_contents = {
                'last_checked': now,
                'subscribers': []
            }
            this_iteration_contents = await Events.load_subscriber_file(file_path, this_iteration_contents)
            if not this_iteration_contents:
                await asyncio.sleep(Events.EVENT_POLL_RATE)
                continue

            if len(this_iteration_contents['subscribers']) == 0:
                print(f'No subscribers to Earthquakes {earthquake_display_string}. Skipping API Call.')
                await asyncio.sleep(Events.EVENT_POLL_RATE)
                continue
            
            new_quakes = await Events.get_earthquakes_since_time(this_iteration_contents['last_checked'], latt, long, radius, min_mag)
            this_iteration_contents['last_checked'] = now

            # write last check time to file
            result = await Events.write_subscriber_file(file_path, this_iteration_contents)
            if not result:
                await asyncio.sleep(Events.EVENT_POLL_RATE)
                continue

            if len(new_quakes) == -1:
                await asyncio.sleep(Events.EVENT_POLL_RATE)
                continue

            # perform announcements
            for quake in new_quakes:
                # (location, mag, time, depth, this_latt, this_long)
                embed = discord.Embed(title=f'{earthquake_display_string} Earthquake: {quake[0]}', url=f'https://www.google.com/maps/@{quake[4]},{quake[5]},10z', color=MessageType.INFO.value)
                embed.add_field(name='Location', value=quake[0], inline=False)
                embed.add_field(name='Magnitude', value=quake[1], inline=True)
                embed.add_field(name='Time', value=datetime.datetime.utcfromtimestamp(quake[2]/1000).strftime('%m/%d/%Y, %H:%M:%S UTC'), inline=True)
                embed.add_field(name='Depth', value=f'{quake[3]}km', inline=True)
                embed.add_field(name='Coordinates', value=f'{round(quake[4], 4)}, {round(quake[5], 4)}', inline=False)
                embed.set_footer(text=f'Message generated at {datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S UTC")}\nThis channel is subscribed to the `EarthquakesGlobal` event')

                for channel in this_iteration_contents.get('subscribers', []):
                    target_channel = commands.get_channel(channel)
                    if target_channel:
                        await target_channel.send(embed=embed)        
                
            # wait for next loop
            await asyncio.sleep(Events.EVENT_POLL_RATE)


    async def write_subscriber_file(file_path, subscriber_object):
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'w') as file:
                    json.dump(subscriber_object, file)
            except Exception as e:
                print(f'There was an error writing to {file_path} after API call: {e}')
                return False
        else:
            return False
        return True


    async def load_subscriber_file(file_path, subscriber_object):
        return_object = subscriber_object
        try:
            if not os.path.isfile(file_path):
                with open(file_path, 'a+') as file:
                    json.dump(return_object, file)
            else:
                with open(file_path, 'r') as file:
                    contents = json.load(file)
                    return_object = contents
        except Exception as e:
            print(f'There was an error processing {file_path} before API call: {e}')
            return False
        return return_object


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
    