# Discord Bots

## DJ-Scoot-A-Zoot
A simple Python-based media player. Allows users to search youtube for videos/music to play in discord voice channels, or link urls from any (audio or video) source to play in voice channels.

### TODO:
* Find ways to reduce time consuming blocking (CPU-bound?) actions:
    * Youtube_DL info extract -> up to 2 seconds
    * Create stream object from FFMPEG -> 2 seconds

## ScootNet
A general-purpose bot that does many things from adding items to databases, get the weather, check for news, or anything else.

## Notes
A universal bot will not be released. When the bots are run, they are each intended to manage one server at a time.

## Installation and Usage

### Required dependencies to `pip install`:

```pip install py-cord ffmpeg asyncio pynacl python-dotenv youtube-search requests "git+https://github.com/ytdl-org/youtube-dl.git" --upgrade py-cord[voice] py-cord[speed]```

### To Run the Music Bot:
```py media.py (server_id from menu)```

For each server that the bot knows about, a list of them will appear on startup. A single server will need to be chosen to serve.

### To Run the Command Bot:
```py bot.py```