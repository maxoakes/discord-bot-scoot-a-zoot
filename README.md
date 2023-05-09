# DJ Scoot-A-Zoot
A general-purpose bot that does many things from adding items to databases, playing music, or talking/chatting with people.

A universal bot will not be released. When the main script is run, it is intended to manage only one server.

If you want to run this bot on multiple servers, you will need to make multiple applications/bots via https://discord.com/developers/applications, and run one script per bot, each with their own token.

Required dependencies to install with pip:
* `discord.py`
* `ffmpeg`
* `asyncio`
* `PyNaCl`
* `dotenv`
* `youtube_dl`
    * `pip install --upgrade --force-reinstall "git+https://github.com/ytdl-org/youtube-dl.git"`

### Quality Testing
```
>>quote direct "This is a direct quote to add" -Scouter, 2023, Discord
>>quote direct "This is a direct quote to add" -Scouter, 2023, Discord
>>quote direct "This is a direct quote to add" -Scouter, 2023,
>>quote direct "This is a direct quote to add" -Scouter, 2023
>>quote direct "This is a direct quote to add" -Scouter
>>quote direct "This is a direct quote to add"
>>quote   add --quote=I am testing a quote. --author=Scouter --location=Discord--time=2023'
>>stream https://allclassical.streamguys1.com/ac128kmp3
>>stream https://www.youtube.com/watch?v=ENSW8Q0u2jw
>>stream https://www.youtube.com/watch?v=TCm9788Tb5g
```