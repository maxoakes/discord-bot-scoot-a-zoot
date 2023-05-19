import os
from dotenv import load_dotenv
from discord import FFmpegOpusAudio, FFmpegPCMAudio
from Util import Util

class MediaManager:

    FFMPEG_OPTS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn -filter:a "volume=0.25"'}
    FILE_PROTOCOL_PREFIX = "file://"
    __voice_client = None
    __current_voice_channel = None

    def __init__(self):
        load_dotenv()

    def set_voice_client(self, voice_client):
        self.__voice_client = voice_client

    def get_voice_client(self):
        return self.__voice_client
    
    def get_voice_channel(self):
        return self.__current_voice_channel
    
    def set_voice_channel(self, channel):
        self.__current_voice_channel = channel

    async def get_stream_from_url(self, source_string: str, is_opus=False):
        # if it is a local file on this computer
        if source_string.find(MediaManager.FILE_PROTOCOL_PREFIX) > -1:
            return FFmpegPCMAudio(executable=os.getenv('FFMPEG_PATH'), source=source_string[len(MediaManager.FILE_PROTOCOL_PREFIX):])
        else:
            if is_opus:
                return await FFmpegOpusAudio.from_probe(MediaManager.get_youtube_playable_link(source_string), executable=os.getenv('FFMPEG_PATH'), **MediaManager.FFMPEG_OPTS, method='fallback')
            else:
                return FFmpegPCMAudio(source=MediaManager.get_youtube_playable_link(source_string), executable=os.getenv('FFMPEG_PATH'), **MediaManager.FFMPEG_OPTS)

    # #################################
    # Static functions
    # #################################

    def get_youtube_playable_link(video_url: str) -> str:
        import youtube_dl
        youtube = youtube_dl.YoutubeDL(Util.YTDL_OPTIONS)
        try:
            info = youtube.extract_info(video_url, download=False)
            return info['formats'][0]['url']
        except Exception as e:
            print(f"ERROR: something went wrong getting info via YTDL. Will assume input string is the direct media URL: {e}")
            return video_url
