import os
import sys
import re
from dotenv import load_dotenv
from cogs.tools import ToolsCog
from cogs.primary import PrimaryCog
from cogs.feeds import FeedCog
from cogs.media import MediaCog
from cogs.quotes import QuoteCog
from state import Program

def main():
    # Parse input
    mode_string = ""
    command_char = ""
    settings_mode = ""
    if len(sys.argv) == 4:
        mode_string = sys.argv[1]
        command_char = sys.argv[2]
        settings_mode = sys.argv[3]
        
    else:
        mode_string = input("Which of the following modes will be activated?" 
                            "\r\n\tm = media"
                            "\r\n\tt = tools"
                            "\r\n\tq = quotes"
                            "\r\n\tr = rss feeds"
                            "\r\nList the letter code(s) of the desired modes: ")
        pattern = re.compile("[\W_]+")
        mode_string = pattern.sub("", mode_string)
        command_char = input("What character will be used as a prefix to denote commands? ")
        settings_mode = input("Will settings be saved to a database (true) or saved to json files (false)? ")
        print(f"Using modes [{mode_string}] with command character [{command_char}] with save method [{settings_mode}]")

    # Initialize settings
    load_dotenv()
    use_database = settings_mode.lower() in Program.AFFIRMATIVE_RESPONSE
    control_channel_id = int(os.getenv("CONTROL_CHANNEL"))
    owner_admin_id = int(os.getenv("YOUR_ID"))
    db_config = {
        "user": os.getenv("MYSQL_USER"),
        "password": os.getenv("MYSQL_PASS"),
        "host": os.getenv("MYSQL_HOST"),
        "database": os.getenv("MYSQL_DB"),
        "raise_on_warnings": True
    }
    Program.initialize(command_char, control_channel_id, owner_admin_id, use_database, db_config=db_config)

    # Start the bot
    token = os.getenv('TOKEN')
    Program.bot.add_cog(PrimaryCog())
    if "t" in mode_string:
        Program.bot.add_cog(ToolsCog())
    if "m" in mode_string:
        Program.bot.add_cog(MediaCog())
    if "r" in mode_string:
        Program.bot.add_cog(FeedCog())
    if "q" in mode_string:
        Program.bot.add_cog(QuoteCog())
    Program.bot.run(token)

    # End
    print("Bot ended naturally.")
    return


if __name__ == "__main__":
    main()

