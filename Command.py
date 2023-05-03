class Command:
    __base = ""
    __primary = ""
    __args = {}

    def __init__(self, input: str):
        # reset
        self.__base = ""
        self.__primary = ""
        self.__args = {}

        # first split between [command and primary] and [list of flags]
        first_flag_index = input.find('--')
        if first_flag_index == -1:
            # there are no flags, just parse the entire input command
            (self.__base, self.__primary) = Command.parse_command_primary(input)
        else:
            # there are flags, so we need to find and split the input command
            (self.__base, self.__primary) = Command.parse_command_primary(input[0:first_flag_index]) 
            arg_string = input[first_flag_index:]

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
        
    def parse_command_primary(input: str):
        items = input.split(' ', 1)
        if len(items) == 1:
            items.append('')
        return (items[0].strip(), items[1].strip())
    
    def get_base_command(self):
        return self.__base
    
    def get_primary_value(self):
        return self.__primary
    
    def get_all_args(self):
        return self.__args

    def get_arg(self, key: str):
        return self.__args.get(key)
    
    def __str__(self):
        return f"COMMAND:'{self.__base}' PRIMARY:'{self.__primary}' FLAG:{self.__args}"