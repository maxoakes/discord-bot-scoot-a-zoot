import datetime
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
        print(f"MainCog.on_ready(): We have logged in as {Program.bot.user}")
        
        if not os.path.exists(Program.GUILD_SETTINGS_DIRECTORY_PATH):
            os.makedirs(Program.GUILD_SETTINGS_DIRECTORY_PATH)

        for guild in Program.bot.guilds:
            # Check if the guild server has a settings file
            if os.path.exists(fr"{Program.GUILD_SETTINGS_DIRECTORY_PATH}/{guild.id}.json"):
                # If so, load it
                guild_instance = GuildInstance(guild.id)
                guild_instance.load_settings_file()
                Program.guild_instances[guild.id] = guild_instance
            else:
                guild_instance = GuildInstance(guild.id)
                guild_instance.write_settings_file()
            

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        print(f"We have logged in as {Program.bot.user}. on_guild_join")
        pass


    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member | discord.User):
        pass


    @commands.command(name="setchannel", hidden=True, 
        brief="Set the channel that bot command responses will be sent to", 
        usage=f"[channel_type] [channel_id] ... NOTE: channel_type must be one of the following: [{','.join(Program.CHANNEL_TYPES)}]")
    async def command_setchannel(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=False):
            return
        if not context.author.guild_permissions.administrator:
            await context.reply(f"Fuck off. You are not an admin.")
        else:
            command = TextCommand(context)

            if len(command.get_all_parts()) == 3:
                channel_type = command.get_part(1)
                if channel_type in Program.CHANNEL_TYPES:
                    channel = Program.bot.get_channel(int(command.get_part(2)))
                    if (channel is not None):
                        await self.assign_channel(channel.guild, channel_type, channel)
                        await context.reply(f"Got it. I will use {channel.mention} for `{channel_type}` messages.")
                    else:
                        await context.reply(f"`{command.get_part(2)}` is not a valid channel ID.")
                else:
                    await context.reply(Program.get_help_instructions("setchannel"))
            else:
                await context.reply(Program.get_help_instructions("setchannel"))


    @commands.command(name="getchannels", hidden=True, brief="Get your server's list of command-like channels")
    async def command_getchannel(self, context: commands.Context):
        if not Utility.is_valid_command_context(context, channel_type=self._default_channel_type, is_global_command=True, is_whisper_command=False):
            return
        if not context.author.guild_permissions.administrator:
            await context.reply(f"Fuck off. You are not an admin.")
        else:
            message_string = "The following channels are used for my message output:\n"
            for channel_type, channel in Program.guild_instances[context.guild.id].get_channels().items():
                message_string += f"`{channel_type}`: {channel.mention}\n"
            await context.reply(message_string)
        

    @commands.command(name="checkchannel", hidden=True, brief="Check if the current channel is of the specified type")
    async def command_checkchannel(self, context: commands.Context):
        command = TextCommand(context)
        channel_type = command.get_part(1)
        if not Utility.is_valid_command_context(context, channel_type=channel_type, is_global_command=False, is_whisper_command=False):
            await context.reply("`fail`")
        else:
            await context.reply("`pass`")


    @commands.command(name="ping", hidden=True, brief="Get a response")
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
        if not context.author.guild_permissions.administrator or not context.channel.permissions_for(context.author).manage_messages:
            await context.reply(f"Incorrect permissions.")
        else:
            command = TextCommand(context)
            do_output = command.get_arg("output") in Program.AFFIRMATIVE_RESPONSE

            if self._cls_running:
                await context.reply(f"This command is already running somewhere and is currently unavailable. Come back later.")
                return
            
            self._cls_running = True
            print(f"Working to delete messages from {context.channel.name}...")
            await context.send(f"Working to delete messages. This may take a while...")
            deleted: list[discord.Message] = await context.channel.purge(oldest_first=True)

            import json
            import re
            output_file_path = ""
            try:
                pattern = re.compile("[\W]+")
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
                print("Channel message dump file written")
            except Exception as e:
                print(f"Failed to write dump: {e}")
                await context.send("Failed creating dump of messages. Exiting command...")
                self._cls_running = False
                return
            finally:
                self._cls_running = False

            if (do_output):
                attachment = discord.File(output_file_path)
                await context.send(f"All messages deleted. Attached is the archive.", file=attachment)


    # #########################
    # Helper Functions
    # #########################

    async def assign_channel(self, guild: discord.Guild, channel_type: str, channel: discord.TextChannel) -> bool:
        guild_id = guild.id
        channel_id = channel.id

        if guild_id in Program.guild_instances:
            Program.guild_instances[guild_id].set_channel_type(channel_type, channel_id)
            print(f"Updated existing guild {guild.name} with {channel_type}:{channel_id}")
        else:
            new_guild_instance = GuildInstance(guild_id)
            new_guild_instance.set_channel_type(channel_type, channel_id)
            Program.guild_instances[guild_id] = new_guild_instance
            print(f"Wrote new guild {guild.name} using {channel_type}:{channel_id}")

        Program.guild_instances[guild_id].write_settings_file()
