from discord.ext import commands
from state import Program   

# #############################
# TextCommand
# #############################

class TextCommand:

    # Private
    _base: list[str] = []
    _args: dict[str, str] = {}
    context: commands.Context

    def __init__(self, context: commands.Context):
        # extract info
        self.context = context
        text = context.message.content[len(Program.command_character):].strip()

        # reset
        self._base = []
        self._args = {}

        # find the split between the command and its flags
        first_flag_index = text.find("--")
        if first_flag_index == -1:
            self._base = text.split(" ")
        else:
            self._base = text[0:first_flag_index].split(" ")
        self._base = list(filter(lambda part: part != "", self._base))

        # if there are flags, parse them
        if first_flag_index > -1:
            # there are flags, so we need to find and split the input command
            arg_string = text[first_flag_index:]

            # parse flag args
            arg_list = arg_string.split("--")[1:]
            for arg in arg_list:
                middle_index = arg.find("=")
                if middle_index == -1:
                    (key, value) = (arg.strip(), None)
                    self._args[key] = value
                else:
                    (key, value) = (arg[0:middle_index].strip(), arg[middle_index+1:].strip())
                    self._args[key] = value
        

    def get_part(self, num: int):
        if num < len(self._base):
            return self._base[num]
        else:
            return ""
    

    def get_command_from(self, start: int):
        # >>quote add "this is a quote"
        #   0.... 1.. 2.... 3. 4 5....
        available_length = len(self._base)
        s = min(start, available_length)
        return " ".join(self._base[s:])
    

    def get_all_args(self):
        return self._args


    def get_arg(self, key: str, default=None):
        return self._args.get(key, default)
    

    def does_arg_exist(self, key: str) -> bool:
        return key in list(self._args.keys())
    

    def get_all_parts(self):
        return self._base
    

    def __str__(self):
        return f"COMMAND:{self._base} FLAG:{self._args}"
