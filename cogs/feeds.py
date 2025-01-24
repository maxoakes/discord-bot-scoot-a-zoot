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

    _settings_filename: str
    _default_channel_type: str
    last_read_date: datetime.datetime
    feed_subscribers: dict[str, FeedSubscriber]

    def __init__(self):
        self._default_channel_type = "rss"
        self._settings_filename = f"{Program.SETTINGS_DIRECTORY_PATH}/{Program.RSS_FEED_SETTINGS_FILE_NAME}"
        self.last_read_date = datetime.datetime.now(datetime.timezone.utc)
        self.feed_subscribers = {}
        

    # on startup
    @commands.Cog.listener()
    async def on_ready(self):
        Program.log(f"FeedCog.on_ready(): We have logged in as {Program.bot.user}",0)

        # load settings
        if Program.use_database:
            self.load_subscribers_from_database()
            Program.log(f"Loaded {len(self.feed_subscribers)} saved RSS feeds from database.",0)
        else:
            if not os.path.exists(Program.SETTINGS_DIRECTORY_PATH):
                os.makedirs(Program.SETTINGS_DIRECTORY_PATH)

            # check if the rss feeds settings file exists
            if not os.path.exists(self._settings_filename):
                # if it does not, create the file
                self.update_subscribers_to_json()
                Program.log(f"Created empty {Program.RSS_FEED_SETTINGS_FILE_NAME}.",1)
            else:
                # if it does read it and load
                self.load_subscribers_from_json()
                Program.log(f"Loaded {len(self.feed_subscribers)} saved feeds(s) from json file.",0)

        # show rss feeds in console
        Program.log(f"RSS feeds last read {self.last_read_date}",0)
        for n, f in self.feed_subscribers.items():
            Program.log(f"  {n}: {json.dumps(f.as_dict())}",0)

        # start rss reader cycle
        await self.rss_watcher()


    async def rss_watcher(self):
        import asyncio
        while True:
            Program.log("Running parse_read() cycle...",0)
            await self.parse_feed()
            await asyncio.sleep(Program.RSS_FEED_UPDATE_TIMER)


    async def parse_feed(self):
        # do feed read
        import feedparser
        for (_, feed_subscriber) in self.feed_subscribers.items():
            url = feed_subscriber.feed_url
            feed = ParsedFeedHeader(feedparser.parse(url))

            new_items: list[ParsedFeedItem] = list(filter(lambda x: datetime.datetime.timestamp(x.published) > datetime.datetime.timestamp(self.last_read_date), feed.items))
            new_items = new_items[0:Program.MAX_NEW_RSS_STORIES_PER_CYCLE] # spam prevention
            Program.log(f"  Parsing {len(new_items)} items from '{feed.title}'. Published after {self.last_read_date} with timestamp({datetime.datetime.timestamp(self.last_read_date)})",0)
            for item in new_items:
                Program.log(f"    Preparing story published {item.published} with timestamp({datetime.datetime.timestamp(item.published)})",0)
                embed = discord.Embed(
                    title=f"{feed.title.upper()} --- {item.title}",
                    color=MessageType.PLAYLIST_ITEM.value,
                    url=item.link,
                    description=item.summary)
                if not Utility.is_null_or_whitespace(feed.image_url):
                    embed.set_thumbnail(url=feed.image_url)
                if (len(item.image_urls) > 0):
                    embed.set_image(url=item.image_urls[0])
                embed.set_footer(text=f"Published {item.published.strftime('%Y-%m-%d %H:%M:%S')}")
                
                for channel_id in feed_subscriber.subscribing_channels:
                    channel = Program.bot.get_channel(channel_id)
                    await channel.send(embed=embed)

        self.last_read_date = datetime.datetime.now(datetime.timezone.utc)
        if Program.use_database:
            self.write_settings_last_read_date_to_database()
        else:
            self.update_subscribers_to_json()
            

    # #####################################
    # Commands
    # #####################################

    @commands.command(name="feeds", hidden=False, brief="Reload from disk the list of RSS feeds, and show them RSS feeds")
    async def command_feeds(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=False):
            return
        
        async with context.typing():
            if Program.use_database:
                self.load_subscribers_from_database()
            else:
                self.load_subscribers_from_json()

        feed_names = list(map(lambda x: f"{x[1].feed_name}: {x[1].feed_url}", self.feed_subscribers.items()))
        feed_string = '\r\n'.join(feed_names)
        await context.send(f"The following RSS feeds are available:\n```{feed_string}```")


    @commands.command(name="subscribe", hidden=False, 
        brief="Subscribe a channel to an RSS feed for updates", 
        usage=f"[rss_feed_name] (channel_id) ... NOTE: use feeds command to get the list of available rss feeds")
    async def command_subscribe(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=False):
            return
        if not context.author.guild_permissions.manage_messages:
            await context.reply(f"You do not have the required permissions: `manage_messages`.")
            return
        
        command = TextCommand(context)
        rss_feed_name = command.get_part(1)
        if not rss_feed_name in list(self.feed_subscribers.keys()):
            await context.reply(f"`{rss_feed_name}` is not a valid feed.")
            return
        
        feed_subscriber = self.feed_subscribers.get(rss_feed_name)
        given_id = command.get_part(2)
        channel_id = context.channel.id
        if not Utility.is_null_or_whitespace(given_id):
            channel_id = int(given_id)

        if Program.bot.get_channel(channel_id) == None:
            await context.reply(f"`{channel_id}` is not a valid channel.")
            return
        
        if channel_id in feed_subscriber.subscribing_channels:
            await context.reply(f"{Program.bot.get_channel(channel_id).mention} is already subscribed to `{rss_feed_name}`.")
            return

        async with context.typing():
            feed_subscriber.subscribing_channels.append(channel_id)
            if Program.use_database:
                self.update_subscriber_to_database(feed_subscriber.feed_name, channel_id)
            else:
                self.update_subscribers_to_json()

        await context.reply(f"Subscribed {Program.bot.get_channel(channel_id).mention} to `{rss_feed_name}`.")
        await Program.write_dev_log(f"Channel {channel_id} was subscribed to `{rss_feed_name}` by `{context.author}`.")

            
    @commands.command(name="unsubscribe", hidden=False, 
        brief="Unsubscribe a channel from an RSS feed", 
        usage=f"[rss_feed_name] (channel_id)")
    async def command_unsubscribe(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=False):
            return
        if not context.author.guild_permissions.manage_messages:
            await context.reply(f"You do not have the required permissions: `manage_messages`.")
            return

        command = TextCommand(context)
        rss_feed_name = command.get_part(1)
        if not rss_feed_name in list(self.feed_subscribers.keys()):
            await context.reply(f"`{rss_feed_name}` is not a valid feed.")
            return
        
        feed_subscriber = self.feed_subscribers.get(rss_feed_name)
        given_id = command.get_part(2)
        channel_id = context.channel.id
        if not Utility.is_null_or_whitespace(given_id):
            channel_id = int(given_id)

        if Program.bot.get_channel(channel_id) == None:
            await context.reply(f"`{channel_id}` is not a valid channel.")
            return
        
        if not channel_id in feed_subscriber.subscribing_channels:
            await context.reply(f"{Program.bot.get_channel(channel_id).mention} is not subscribed to `{rss_feed_name}`.")
            return
        
        async with context.typing():
            feed_subscriber.subscribing_channels.remove(channel_id)
            if Program.use_database:
                self.remove_subscriber_from_database(feed_subscriber.feed_name, channel_id)
            else:
                self.update_subscribers_to_json()

        await context.reply(f"Unsubscribed {Program.bot.get_channel(channel_id).mention} from `{rss_feed_name}`.")
        await Program.write_dev_log(f"Channel {channel_id} was unsubscribed from `{rss_feed_name}` by `{context.author}`.")


    # #########################
    # Helper Functions
    # #########################

    def update_subscribers_to_json(self):
        data = {
            "last_read": self.last_read_date.isoformat(),
            "feed_subscribers": list(map(lambda x: x[1].as_dict(), self.feed_subscribers.items()))
        }
        
        with open(self._settings_filename, "w") as file:
            json.dump(data, file, indent=4)
            Program.log(f"Wrote to {self._settings_filename}",0)
                

    def load_subscribers_from_json(self) -> bool:
        with open(self._settings_filename) as file:
            from dateutil import parser
            settings = json.load(file)
            self.last_read_date = parser.parse(settings.get("last_read", datetime.datetime.now(datetime.timezone.utc).isoformat()))
            feed_subscribers = settings.get("feed_subscribers", [])
            self.feed_subscribers = {}
            for fs in feed_subscribers:
                feed_name = fs.get("feed_name", None)
                if feed_name != None:
                    self.feed_subscribers[feed_name] = FeedSubscriber(
                        fs.get("feed_name", "name"),
                        fs.get("feed_url", "about:blank"),
                        fs.get("subscribing_channels", [])
                    )
                else:
                    Program.log(f"Invalid FeedSubscriber from file: {feed_name}",2)
            Program.log(f"Loaded {self._settings_filename}",0)
                

    def update_subscriber_to_database(self, feed_name: str, channel_id: int):
        return Program.call_procedure_return_scalar("subscribe_to_rss_feed", (feed_name, channel_id))
    

    def remove_subscriber_from_database(self, feed_name: str, channel_id: int):
        return Program.call_procedure_return_scalar("unsubscribe_to_rss_feed", (feed_name, channel_id))
    

    def load_subscribers_from_database(self):
        feeds_rows = Program.run_query_return_rows("SELECT unique_name, url FROM discord.rss_feeds")
        self.feed_subscribers.clear()
        for unique_name, url in feeds_rows:
            self.feed_subscribers[unique_name] = FeedSubscriber(unique_name, url, [])

        subscribers_rows = Program.run_query_return_rows("SELECT f.unique_name, s.channel_id FROM discord.rss_feed_subscribers AS s LEFT JOIN discord.rss_feeds AS f ON s.rss_feed_id=f.id")
        for unique_name, channel_id in subscribers_rows:
            self.feed_subscribers.get(unique_name).subscribing_channels.append(channel_id)

        settings_rows = Program.run_query_return_rows("SELECT * FROM discord.settings")
        for name, value in settings_rows:
            if name == "last_read_date":
                self.last_read_date = datetime.datetime.fromisoformat(value)
                Program.log(f"Parsed '{value}' to [{self.last_read_date}] from database")


    def write_settings_last_read_date_to_database(self):
        return Program.call_procedure_return_scalar("insert_or_update_settings", ("last_read_date", str(self.last_read_date)))
