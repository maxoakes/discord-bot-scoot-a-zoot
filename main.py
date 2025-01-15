import os
import sys
import re
from dotenv import load_dotenv
from cogs.tools import ToolsCog
from cogs.primary import PrimaryCog
from cogs.feeds import FeedCog
from cogs.media import MediaCog
from state import Program

def main():
    # Parse input
    mode_string = ""
    command_char = ""
    if len(sys.argv) == 3:
        mode_string = sys.argv[1]
        command_char = sys.argv[2]
    else:
        mode_string = input("Which of the following modes will be activated?" 
                            "\r\n\tm = media"
                            "\r\n\tt = tools"
                            "\r\n\tq = quotes"
                            "\r\n\tr = rss feeds"
                            "\r\nList the letter code(s) of the desired modes: ")
        pattern = re.compile("[\W_]+")
        mode_string = pattern.sub("", mode_string)
        command_char = input('What character will be used as a prefix to denote commands? ')
        print(f"Using modes [{mode_string}] with command character [{command_char}]")

    # Initialize settings
    load_dotenv()
    control_channel_id = int(os.getenv('CONTROL_CHANNEL'))
    Program.initialize(command_char, control_channel_id)

    # Start the bot
    token = os.getenv('TOKEN')
    Program.bot.add_cog(PrimaryCog())
    if "t" in mode_string:
        Program.bot.add_cog(ToolsCog())
    if "r" in mode_string:
        Program.bot.add_cog(FeedCog())
    if "m" in mode_string:
        Program.bot.add_cog(MediaCog())
    Program.bot.run(token)

    # End
    print("Bot ended naturally.")
    return


if __name__ == "__main__":
    main()

