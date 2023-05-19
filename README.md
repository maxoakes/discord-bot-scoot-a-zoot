# DJ Scoot-A-Zoot
A general-purpose bot that does many things from adding items to databases, playing music, or talking/chatting with people.

A universal bot will not be released. When the main script is run, it is intended to manage only one server.

If you want to run this bot on multiple servers, you will need to make multiple applications/bots via https://discord.com/developers/applications, and run one script per bot, each with their own token.

Required dependencies to `pip install`:
* `discord.py`
* `ffmpeg`
* `asyncio`
* `PyNaCl`
* `python-dotenv`
* `youtube_dl`
    * `pip install --upgrade --force-reinstall "git+https://github.com/ytdl-org/youtube-dl.git"`
* `youtube-search`
* `requests`

```pip install discord.py ffmpeg asyncio pynacl python-dotenv youtube-search requests --upgrade --force-reinstall "git+https://github.com/ytdl-org/youtube-dl.git"```

TODO:
* Find reason and solution to time delay between song request and song playing in voice channel
    * Youtube_DL info extract -> 2 seconds
    * Create stream object from FFMPEG -> 2 seconds
    * Youtube search from keywords -> 0.8 seconds