from pathlib import Path

class Help:
    text_commands = ['quote']
    media_commands = ['search', 'stream', 'next', 'prev', 'playlist', 'clear', 'end', 'pause', 'resume', 'preset']
    
    def get_dj_help_markdown(command_name: str):
        comm = command_name.lower()
        out = ""
        match comm:
            case 'search' | 'stream' | 'next' | 'prev' | 'playlist' | 'clear' | 'end' | 'pause' | 'resume':
                out = Path(f'help/{comm}.md').read_text()
            case 'preset' | 'presets':
                import csv
                preset_list = ""
                try:
                    with open('presets.csv', newline='', encoding='utf-8') as file:
                        reader = csv.reader(file)
                        for i, row in enumerate(reader):
                            # print(row) # [preset, url, desc]
                            if row[0].lower() != 'preset':
                                preset_list = preset_list + f"\n {i}. `{row[0]}` {row[2]}"
                    out = f"**The following presets are available when requesting media streams in the format `>>stream --preset=<preset_name>`:**\n{preset_list}"
                except:
                    out = "There was a problem reading the presets file."
            case "" | _:
                out = "**Available commands are:**"
                for i, c in enumerate(Help.media_commands):
                    out = out + f"\n{i+1}. `{c}`"
                out = out + f"\n**Use `>>help <command>` to learn more**"
        return out
    
    def get_text_help_markdown(command_name: str):
        comm = command_name.lower()
        out = ""
        match comm:
            case 'quote':
                out = Path(f'help/{comm}.md').read_text()
            case "" | _:
                out = "**Available commands are:**"
                for i, c in enumerate(Help.text_commands):
                    out = out + f"\n{i+1}. `{c}`"
                out = out + f"\n**Use `>>help <command>` to learn more**"
        return out