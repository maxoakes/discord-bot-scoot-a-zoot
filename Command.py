import discord

class Command:
    # final static
    COMMAND_CHAR = '>>'

    # private variables
    __base: list[str] = []
    __args: dict[str, str] = {}

    __text: str = ""
    __message: discord.Message
    __author: discord.Member | discord.User = None
    __channel = None

    def __init__(self, message: discord.Message):
        # extract info
        self.__author = message.author
        self.__channel = message.channel
        self.__message = message
        self.__text = message.content[len(Command.COMMAND_CHAR):].strip()

        # reset
        self.__base = []
        self.__args = {}

        # find the split between the command and its flags
        first_flag_index = self.__text.find('--')
        if first_flag_index == -1:
            self.__base = self.__text.split(' ')
        else:
            self.__base = self.__text[0:first_flag_index].split(' ')
        self.__base = list(filter(lambda part: part != '', self.__base))

        # if there are flags, parse them
        if first_flag_index > -1:
            # there are flags, so we need to find and split the input command
            arg_string = self.__text[first_flag_index:]

            # parse flag args
            arg_list = arg_string.split('--')[1:]
            for arg in arg_list:
                middle_index = arg.find('=')
                if middle_index == -1:
                    (key, value) = (arg.strip(), None)
                    self.__args[key] = value
                else:
                    (key, value) = (arg[0:middle_index].strip(), arg[middle_index+1:].strip())
                    self.__args[key] = value
        
    def get_part(self, num: int):
        return self.__base[num]
    
    def get_command_from(self, start: int):
        # >>quote add "this is a quote"
        #   0     1   2     3  4 5
        available_length = len(self.__base)
        s = min(start, available_length)
        return ' '.join(self.__base[s:])
    
    def get_all_args(self):
        return self.__args

    def get_arg(self, key: str):
        return self.__args.get(key)
    
    def does_arg_exist(self, key: str) -> bool:
        return key in list(self.__args.keys())

    def get_author(self):
        return self.__author
    
    def get_channel(self):
        return self.__channel
    
    def get_message(self):
        return self.__message
    
    def __str__(self):
        return f"COMMAND:{self.__base} FLAG:{self.__args}"