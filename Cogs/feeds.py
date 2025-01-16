import datetime
import json
import discord
import os
from discord.ext import commands
from classes.parsed_feed import ParsedFeedItem, ParsedFeedHeader
from classes.feed_subscriber import FeedSubscriber
from classes.text_command import TextCommand
from state import MessageType, Program, Utility

class FeedCog(commands.Cog):

    _default_channel_type: str
    _last_read_date: datetime.datetime
    _feed_subscribers: dict[str, FeedSubscriber]

    def __init__(self):
        self._default_channel_type = "rss"
        self._update_rate = 60*30
        self._last_read_date = datetime.datetime.now(datetime.timezone.utc)
        self._feed_subscribers = {}
        

    # on startup
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"FeedCog.on_ready(): We have logged in as {Program.bot.user}")

        filename = f"{Program.SETTINGS_DIRECTORY_PATH}/{Program.RSS_FEED_SETTINGS_FILE_NAME}"
        if not os.path.exists(Program.SETTINGS_DIRECTORY_PATH):
            os.makedirs(Program.SETTINGS_DIRECTORY_PATH)
        if not os.path.isfile(filename):
            self.write_rss_settings()
        self.load_rss_settings()
        self.print_rss_settings_local_cache()
        await self.rss_watcher()


    async def rss_watcher(self):
        import asyncio
        while True:
            print("Running parse_read() cycle...")
            await self.parse_feed()
            await asyncio.sleep(self._update_rate)


    async def parse_feed(self):
        # do feed read
        import feedparser
        for (_, feed_subscriber) in self._feed_subscribers.items():
            url = feed_subscriber.feed_url
            feed = ParsedFeedHeader(feedparser.parse(url))

            new_items: list[ParsedFeedItem] = list(filter(lambda x: datetime.datetime.timestamp(x.published) > datetime.datetime.timestamp(self._last_read_date), feed.items))
            new_items = new_items[0:Program.MAX_NEW_RSS_STORIES_PER_CYCLE] # spam spam prevention
            print(f"Parsing {len(new_items)} items from '{feed.title}'. These are published after {self._last_read_date} with timestamp({datetime.datetime.timestamp(self._last_read_date)})")
            for item in new_items:
                print(f"\tPreparing story published {item.published} with timestamp({datetime.datetime.timestamp(item.published)})")
                embed = discord.Embed(
                    title=item.title, 
                    color=MessageType.PLAYLIST_ITEM.value,
                    url=item.link,
                    description=item.summary)
                embed.set_thumbnail(url=feed.image_url)
                if (len(item.image_urls) > 0):
                    embed.set_image(url=item.image_urls[0])
                embed.set_footer(text=f"Published {item.published.strftime('%Y-%m-%d %H:%M:%S')}")
                
                for channel_id in feed_subscriber.subscribing_channels:
                    channel = Program.bot.get_channel(channel_id)
                    await channel.send(embed=embed)

        self._last_read_date = datetime.datetime.now(datetime.timezone.utc)
        self.write_rss_settings()
            

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        print(f"We have logged in as {Program.bot.user}. on_guild_join")
        pass


    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member | discord.User):
        pass


    @commands.command(name="feeds", hidden=False, brief="Get a list of available RSS feeds")
    async def command_feeds(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=False):
            return
        
        string_list = ""
        feed_names = list(map(lambda x: f"{x[1].feed_name}: \t{x[1].feed_url}", self._feed_subscribers.items()))
        await context.send(f"The following RSS feeds are available:\n```{feed_names}```")


    @commands.command(name="feed", hidden=False, 
        brief="Add or remove an RSS feed",
        usage=f"[add|remove] [rss_feed_name] (rss_url) ... NOTE: use feeds command to get the list of available rss feeds")
    async def command_feed(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=False):
            return
        
        if not context.author.guild_permissions.administrator:
            await context.reply(f"You must be an admin to use this command.")
        else:
            command = TextCommand(context)

        feed_name = command.get_part(2)
        if command.get_part(1).lower() == "add":
            url = command.get_part(3)
            if Utility.is_null_or_whitespace(url):
                await context.reply(Program.get_help_instructions("feed"))
            
            if self._feed_subscribers.get(feed_name, None) == None:
                self._feed_subscribers[feed_name] = FeedSubscriber(feed_name, url, [])
                await context.reply(f"`{feed_name}` has been added using `{url}`.")
                self.write_rss_settings()
                await Program.write_dev_log(f"Feed type `{feed_name}`: `{url}` was added by `{context.author}`.")
            else:
                await context.reply(f"There is already a feed by the name `{feed_name}`.")

        elif command.get_part(1).lower() == "remove":
            if self._feed_subscribers.get(feed_name, None) == None:
                await context.reply(f"There is no feed by the name of `{feed_name}`.")
            else:
                self._feed_subscribers.pop(feed_name)
                await context.reply(f"`{feed_name}` has been removed.")
                self.write_rss_settings()
                await Program.write_dev_log(f"Feed type `{feed_name}` was removed by `{context.author}`.")
        else:
            await context.reply(Program.get_help_instructions("feed"))
            return


    @commands.command(name="subscribe", hidden=False, 
        brief="Subscribe a channel to an RSS feed for updates", 
        usage=f"[rss_feed_name] (channel_id) ... NOTE: use feeds command to get the list of available rss feeds")
    async def command_subscribe(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=False):
            return
        if not context.author.guild_permissions.administrator:
            await context.reply(f"You must be an admin to use this command.")
        else:
            command = TextCommand(context)
            rss_feed_name = command.get_part(1)
            try:
                if not rss_feed_name in list(self._feed_subscribers.keys()):
                    await context.reply(f"`{rss_feed_name}` is not a valid feed.")
                    return
                feed_subscriber = self._feed_subscribers.get(rss_feed_name)
                given_id = command.get_part(2)
                channel_id = context.channel.id
                if not Utility.is_null_or_whitespace(given_id):
                    channel_id = int(given_id)

                if Program.bot.get_channel(channel_id) == None:
                    await context.reply(f"`{channel_id}` is not a valid channel.")
                    return
                if channel_id in feed_subscriber.subscribing_channels:
                    await context.reply(f"{Program.bot.get_channel(channel_id).mention} is already subscribed to `{rss_feed_name}`.")
                else:
                    feed_subscriber.subscribing_channels.append(channel_id)
                    self.write_rss_settings()
                    await context.reply(f"Subscribed {Program.bot.get_channel(channel_id).mention} to `{rss_feed_name}`.")
                    await Program.write_dev_log(f"Channel {channel_id} was subscribed to `{rss_feed_name}` by `{context.author}`.")
            except Exception as e:
                await context.reply(f"Something went wrong subscribing.")
                print(e)
                return
            
    
    @commands.command(name="unsubscribe", hidden=False, 
        brief="Unsubscribe a channel from an RSS feed", 
        usage=f"[rss_feed_name] (channel_id)")
    async def command_unsubscribe(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=False):
            return
        if not context.author.guild_permissions.administrator:
            await context.reply(f"You must be an admin to use this command.")
        else:
            command = TextCommand(context)
            rss_feed_name = command.get_part(1)
            try:
                if not rss_feed_name in list(self._feed_subscribers.keys()):
                    await context.reply(f"`{rss_feed_name}` is not a valid feed.")
                    return
                feed_subscriber = self._feed_subscribers.get(rss_feed_name)
                given_id = command.get_part(2)
                channel_id = context.channel.id
                if not Utility.is_null_or_whitespace(given_id):
                    channel_id = int(given_id)

                if Program.bot.get_channel(channel_id) == None:
                    await context.reply(f"`{channel_id}` is not a valid channel.")
                    return
                if not channel_id in feed_subscriber.subscribing_channels:
                    await context.reply(f"{Program.bot.get_channel(channel_id).mention} is not subscribed to `{rss_feed_name}`.")
                else:
                    feed_subscriber.subscribing_channels.remove(channel_id)
                    self.write_rss_settings()
                    await context.reply(f"Unsubscribed {Program.bot.get_channel(channel_id).mention} from `{rss_feed_name}`.")
                    await Program.write_dev_log(f"Channel {channel_id} was unsubscribed from `{rss_feed_name}` by `{context.author}`.")
            except Exception as e:
                await context.reply(f"Something went wrong unsubscribing.")
                print(e)
                return


    @commands.command(name="force_read", hidden=False, 
        brief="Force a pass of the rss reader to all channels")
    async def command_force_read(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=False):
            return
        if not context.author.guild_permissions.administrator:
            await context.reply(f"You must be an admin to use this command.")
        print(f"{context.author.name} forced a rss feed update.")
        await self.parse_feed()


    # #########################
    # Helper Functions
    # #########################

    def write_rss_settings(self):
        filename = f"{Program.SETTINGS_DIRECTORY_PATH}/{Program.RSS_FEED_SETTINGS_FILE_NAME}"
        data = {
            "last_read": self._last_read_date.isoformat(),
            "update_rate": self._update_rate,
            "feed_subscribers": list(map(lambda x: x[1].as_dict(), self._feed_subscribers.items()))
        }
        
        with open(filename, "w") as file:
            json.dump(data, file, indent=4)
            print(f"Wrote to {filename} at {datetime.datetime.now()}")
                

    def load_rss_settings(self) -> bool:
        filename = f"{Program.SETTINGS_DIRECTORY_PATH}/{Program.RSS_FEED_SETTINGS_FILE_NAME}"
        if os.path.isfile(filename):
            with open(filename) as file:
                from dateutil import parser
                settings = json.load(file)
                self._last_read_date = parser.parse(settings.get("last_read", datetime.datetime.now(datetime.timezone.utc).isoformat()))
                self._update_rate = settings.get("update_rate", 1800)
                feed_subscribers = settings.get("feed_subscribers", [])
                self._feed_subscribers = {}
                for fs in feed_subscribers:
                    feed_name = fs.get("feed_name", None)
                    if feed_name != None:
                        self._feed_subscribers[feed_name] = FeedSubscriber(
                            fs.get("feed_name", "name"),
                            fs.get("feed_url", "about:blank"),
                            fs.get("subscribing_channels", [])
                        )
                    else:
                        print(f"Invalid FeedSubscriber from file: {feed_name}")
                print(f"Loaded {filename} at {datetime.datetime.now()}")
        else:
            print(f"Filepath does not exist: {filename}")
            self.write_rss_settings()
                

    def print_rss_settings_local_cache(self):
        print(f"RSS Settings -> last read: {self._last_read_date}")
        print(f"RSS Settings -> update rate: {self._update_rate}")
        print(f"RSS Settings -> feeds: {list(map(lambda x: x[1].as_dict(), self._feed_subscribers.items()))}")
