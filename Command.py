class Command:
    __base: list[str] = []
    __args: dict[str, str] = {}

    __original: str = ""

    def __init__(self, input: str):
        # reset
        self.__original = input.strip()
        self.__base = []
        self.__args = {}

        # find the split between the command and its flags
        first_flag_index = self.__original.find('--')
        if first_flag_index == -1:
            self.__base = self.__original.split(' ')
        else:
            self.__base = self.__original[0:first_flag_index].split(' ')
        self.__base = list(filter(lambda part: part != '', self.__base))
        print(self.__base)

        # if there are flags, parse them
        if first_flag_index > -1:
            # there are flags, so we need to find and split the input command
            arg_string = self.__original[first_flag_index:]

            # parse flag args
            arg_list = arg_string.split('--')[1:]
            print(arg_list)
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
        available_lenth = len(self.__base)
        s = min(start, available_lenth)
        return ' '.join(self.__base[s:])
    
    def get_all_args(self):
        return self.__args

    def get_arg(self, key: str):
        return self.__args.get(key)
    
    def __str__(self):
        return f"COMMAND:{self.__base} FLAG:{self.__args}"