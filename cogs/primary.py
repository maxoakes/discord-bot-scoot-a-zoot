import datetime
import json
import discord
import os
from discord.ext import commands
from classes.guild_instance import GuildInstance
from classes.text_command import TextCommand
from state import Program, Utility

class PrimaryCog(commands.Cog):

    _default_channel_type: str
    _cls_running: bool

    def __init__(self):
        self._default_channel_type = "command"
        self._cls_running = False

    # on startup
    @commands.Cog.listener()
    async def on_ready(self):
        Program.log(f"MainCog.on_ready(): We have logged in as {Program.bot.user}",0)

        if Program.use_database:
            self.load_guilds_from_database()
            Program.log(f"Loaded {len(Program.guild_instances)} saved guild(s) from database.",0)
        else:
            # make the settings directory if it does not exist
            if not os.path.exists(Program.SETTINGS_DIRECTORY_PATH):
                os.makedirs(Program.SETTINGS_DIRECTORY_PATH)

            # check if the guild settings file exists
            if not os.path.exists(f"{Program.SETTINGS_DIRECTORY_PATH}/{Program.GUILD_SETTINGS_FILE_NAME}"):
                # if it does not, create the file
                self.write_guilds_to_json()
                Program.log(f"Created empty {Program.GUILD_SETTINGS_FILE_NAME}.",1)
            else:
                # if it does read it and load
                self.load_guilds_from_json()
                Program.log(f"Loaded {len(Program.guild_instances)} saved guild(s) from json file.",0)

        # show guilds in console
        for i, g in Program.guild_instances.items():
            Program.log(f"  {i}: {json.dumps(g.as_dict())}",0)

        # iterate through all connected guilds and add them to the guild instance list
        for guild in Program.bot.guilds:
            if Program.guild_instances.get(guild.id, None) == None:
                Program.guild_instances[guild.id] = GuildInstance(guild.id)
                Program.log(f"Added {guild} to internal guild_instance dict.",0)
            

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        Program.log(f"We have logged in as {Program.bot.user} to {guild.name}.",0)
        Program.guild_instances[guild.id] = GuildInstance(guild.id)
        pass


    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member | discord.User):
        pass


    @commands.command(name="setchannel", hidden=False, 
        brief="Set the channel that bot command responses will be sent to", 
        usage=f"[channel_type] [channel_id] ... NOTE: channel_type must be one of the following: [{','.join(Program.CHANNEL_TYPES)}]")
    async def command_setchannel(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=False):
            return
        if not context.author.guild_permissions.manage_messages:
            await context.reply(f"You do not have the required permissions: `manage_messages`.")
            return

        command = TextCommand(context)
        # show instructions if wrong syntax
        if len(command.get_all_parts()) != 3:
            await context.reply(Program.get_help_instructions("setchannel"))
            return
        
        # show instructions if invalid channel type
        channel_type = command.get_part(1)
        if not channel_type in Program.CHANNEL_TYPES:
            await context.reply(Program.get_help_instructions("setchannel"))
            return
        
        # return if channel is not valid
        channel = Program.bot.get_channel(int(command.get_part(2)))
        if channel == None:
            await context.reply(f"`{command.get_part(2)}` is not a valid channel ID.")
            return
        
        # if the command is all valid
        async with context.typing():
            guild_id = channel.guild.id
            channel_id = channel.id

            if guild_id in Program.guild_instances:
                Program.guild_instances[guild_id].set_channel_type(channel_type, channel_id)
                Program.log(f"Updated existing guild {channel.guild.name} with {channel_type} channel as {channel_id}",0)
            else:
                new_guild_instance = GuildInstance(guild_id)
                new_guild_instance.set_channel_type(channel_type, channel_id)
                Program.guild_instances[guild_id] = new_guild_instance
                Program.log(f"Wrote new guild {channel.guild.name} using {channel_type}:{channel_id}",0)

            # save change to disk
            if Program.use_database:
                result = self.update_guilds_to_database(guild_id, channel_type, channel_id)
                if result != 1:
                    await context.reply(f"Something went wrong ({result})")
                    Program.log(f"Something went wrong ({result})",3)
                    return
            else:
                self.write_guilds_to_json()

        # final response to user
        await context.reply(f"Got it. I will use {channel.mention} for `{channel_type}` messages.")                   


    @commands.command(name="getchannels", hidden=False, brief="Get your server's list of command-like channels")
    async def command_getchannel(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=False):
            return
        
        message_string = "The following channels are used for my message output:\n"
        for channel_type, channel in Program.guild_instances[context.guild.id].get_channels().items():
            message_string += f"`{channel_type}`: {channel.mention}\n"
        await context.reply(message_string)
        

    @commands.command(name="checkchannel", hidden=False, brief="Check if the current channel is of the specified type")
    async def command_checkchannel(self, context: commands.Context):
        command = TextCommand(context)
        channel_type = command.get_part(1)
        if not Utility.is_valid_command_context(context, channel_type=channel_type, is_global_command=False, is_whisper_command=False):
            await context.reply("`fail`")
        else:
            await context.reply("`pass`")


    @commands.command(name="ping", hidden=False, brief="Get a response")
    async def command_ping(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=True):
            return
        await context.reply(f"pong\n```{datetime.datetime.now().timestamp() - context.message.created_at.timestamp()} ms```")


    @commands.command(name="cls", hidden=True, 
        brief="Delete and archive all messages in this channel",
        usage="(--output=[yes|no])",
        description="Delete and (optionally) archive all messages in this channel. Only one instance of this action can occur globally at one time.")
    async def command_cls(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=False):
            return
        if not context.author.guild_permissions.manage_messages:
            await context.reply(f"You do not have the required permissions: `manage_messages`.")
            return

        command = TextCommand(context)
        do_output = command.get_arg("output") in Program.AFFIRMATIVE_RESPONSE

        if self._cls_running:
            await context.reply(f"This command is already running somewhere and is currently unavailable. Come back later.")
            return
        
        self._cls_running = True
        Program.log(f"Working to delete messages from {context.channel.name}...",1)
        await context.send(f"Working to delete messages. This may take a while...")
        deleted: list[discord.Message] = await context.channel.purge(oldest_first=True)

        import json
        import re
        output_file_path = ""
        try:
            pattern = re.compile(r"[\W]+")
            output_file_name = f"messages_{context.guild.name}_{context.channel.name}_{round(datetime.datetime.now().timestamp())}"
            output_file_name = pattern.sub("", output_file_name)
            output_file_path = fr"logs/{output_file_name}.json"
            with open(output_file_path, "w") as file:
                output_list = []
                for m in deleted:
                    output_list.append(dict(map(lambda kv: (kv[0], str(kv[1])), {
                        "id": m.id,
                        "guild": m.guild,
                        "channel": m.channel.name,
                        "content": m.content,
                        "author": m.author,
                        "created_at": m.created_at,
                        "edited_at": m.edited_at,
                        "components": m.components,
                        "pinned": m.pinned,
                        "type": m.type,
                        "tts": m.tts,
                        "activity": m.activity,
                        "attachments": m.attachments,
                        "embeds": m.embeds,
                        "application": m.application
                    }.items())))
                json.dump(output_list, file, indent=4)
            Program.log(f"Channel message dump written to file {output_file_name}",1)
        except Exception as e:
            Program.log(f"Failed to write dump: {e}",2)
            await context.send("Failed creating dump of messages. Exiting command...")
            self._cls_running = False
            return
        finally:
            self._cls_running = False

        if (do_output):
            attachment = discord.File(output_file_path)
            await context.send(f"All messages deleted. Attached is the archive.", file=attachment)


    # #########################
    # I/O functions
    # #########################

    def write_guilds_to_json(self):
        filepath = fr"{Program.SETTINGS_DIRECTORY_PATH}/{Program.GUILD_SETTINGS_FILE_NAME}"
        package = {k: v.as_dict() for k, v in Program.guild_instances.items()}
        with open(filepath, "w") as file:
            json.dump(package, file, indent=4)
        Program.log(f"\tWrote to {filepath}",0)

    
    def load_guilds_from_json(self):
        filepath = fr"{Program.SETTINGS_DIRECTORY_PATH}/{Program.GUILD_SETTINGS_FILE_NAME}"
        with open(filepath) as file:
            settings = json.load(file)
            Program.guild_instances.clear()
            for guild_id, raw_dict in settings:
                guild_instance = GuildInstance(guild_id)
                for channel_type, channel_id in raw_dict.items():
                    guild_instance.set_channel_type(channel_type, channel_id)
                Program.guild_instances[guild_id] = guild_instance


    def update_guilds_to_database(self, guild_id, channel_type, channel_id):
        return Program.call_procedure_return_scalar("insert_or_update_guild_channel", (guild_id, channel_type, channel_id))
    

    def load_guilds_from_database(self):
        rows = Program.run_query_return_rows("SELECT guild_id, channel_type, channel_id FROM guild_channels")
        for guild_id, channel_type, channel_id in rows:
            if Program.guild_instances.get(guild_id):
                Program.guild_instances[guild_id].set_channel_type(channel_type, channel_id)
            else:
                guild_instance = GuildInstance(guild_id)
                guild_instance.set_channel_type(channel_type, channel_id)
                Program.guild_instances[guild_id] = guild_instance
