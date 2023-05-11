from pathlib import Path
from Util import Util

class Help:
    commands = ['quote', 'stream', 'next', 'prev', 'playlist', 'clear', 'end', 'pause', 'resume', 'preset']
    
    def get_help_markdown(command_name: str):
        single_command = command_name.replace('\\', '').replace('/','') # need to avoid malicious behavior
        match single_command:
            case 'quote' | 'stream' | 'next' | 'prev' | 'playlist' | 'clear' | 'end' | 'pause' | 'resume':
                out = Path(f'help/{single_command}.md').read_text()
            case 'preset' | 'presets':
                import csv
                preset_list = ""
                try:
                    with open('presets.csv', newline='', encoding='utf-8') as file:
                        reader = csv.reader(file)
                        for i, row in enumerate(reader):
                            # print(row) # [preset, url, is_vid, desc]
                            if row[0].lower() != 'preset':
                                preset_list = preset_list + f"\n {i}. `{row[0]}` {row[3]}:"
                                preset_list = preset_list = (preset_list + " (Video)") if row[2] in Util.AFFIRMATIVE_RESPONSE else (preset_list + " (Audio)")
                    out = f"**The following presets are available when requesting media streams in the format `>>stream --preset=<preset_name>`:**\n{preset_list}"
                except:
                    out = "There was a problem reading the presets file."

            case "" | _:
                out = "**Available commands are:**"
                for i, c in enumerate(Help.commands):
                    out = out + f"\n{i+1}. `{c}`"
                out = out + f"\n**Use `>>help <command>` to learn more**"
        return out