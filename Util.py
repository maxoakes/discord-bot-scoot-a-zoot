from enum import Enum

class Util:
    BOT_COMMAND_CHANNEL_NAMES = ['bot-spam', 'bot-commands', 'botspam', '']
    MEDIA_REQUEST_CHANNEL_NAMES = ['jukebox', 'music-requests', 'dj-requests']
    AFFIRMATIVE_RESPONSE = ['y', 'ya', 'ye', 'yea', 'yes', 'yeah', 't', 'true']
    NEGATIVE_RESPONSE = ['n', 'no', 'nah', 'neah', 'f', 'false']
    END_RESPONSE = ['s', 'stop', 'e', 'end', 'exit', 'h', 'halt']
    FFMPEG_PATH = r"A:/Programs/ffmpeg/bin/ffmpeg.exe"
    FILE_PROTOCOL_PREFIX = "file://"
    YOUTUBE_URL_PREFIX_FULL = "https://www.youtube.com/watch?"
    YOUTUBE_URL_PREFIX_SHORT = "https://youtu.be/"

class PlaylistAction(Enum):
    STAY = 0
    FORWARD = 1
    BACKWARD = 2
    STOP = 3