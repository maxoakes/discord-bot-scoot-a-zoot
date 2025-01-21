
import datetime
import json
import os

from dotenv import load_dotenv
from classes.quote import Quote
from state import Program, Utility


def main():
    load_dotenv()
    db_config = {
        "user": os.getenv("MYSQL_USER"),
        "password": os.getenv("MYSQL_PASS"),
        "host": os.getenv("MYSQL_HOST"),
        "database": os.getenv("MYSQL_DB"),
        "raise_on_warnings": True
    }
    Program.db_config = db_config

    guild_id = 350330699192074250
    with open('quotes.json', 'r') as f:
        data = json.load(f)
        i = 0
        l = len(data)
        for set in data:
            hash = datetime.datetime.now().timestamp().__hash__() + i
            i = i + 1
            j = 1
            for q in set:
                quote = q.get("quote", None)
                author = q.get("author", None)
                time_place = q.get("time_place", None)
                result = Program.call_procedure_return_scalar("insert_quote_with_set_id", (hash, j, guild_id, quote, author, time_place))
                print(f"{i}/{l}. result:{result} unique:{hash}")
                j = j + 1

if __name__ == "__main__":
    main()
