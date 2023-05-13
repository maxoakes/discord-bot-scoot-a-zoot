from discord import FFmpegOpusAudio, FFmpegPCMAudio
from Util import Util

class MediaManager:

    __voice_client = None
    __current_voice_channel = None

    def __init__(self):
        pass

    def set_voice_client(self, voice_client):
        self.__voice_client = voice_client

    def get_voice_client(self):
        return self.__voice_client
    
    def get_voice_channel(self):
        return self.__current_voice_channel
    
    def set_voice_channel(self, channel):
        self.__current_voice_channel = channel
    
    async def get_stream_from_url(self, source_string: str):
        # if it is a youtube video
        if source_string.find(Util.YOUTUBE_URL_PREFIX_FULL) > -1 or source_string.find(Util.YOUTUBE_URL_PREFIX_SHORT) > -1:
            return FFmpegPCMAudio(Util.get_youtube_playable_link(source_string), **Util.FFMPEG_OPTS)
        # if it is a local file on this computer
        elif source_string.find(Util.FILE_PROTOCOL_PREFIX) > -1:
            return FFmpegPCMAudio(executable=Util.FFMPEG_PATH, source=Util.get_file_location_from_url(source_string))
        # if it is some other location
        else:
            return await FFmpegOpusAudio.from_probe(source_string, **Util.FFMPEG_OPTS, method='fallback')