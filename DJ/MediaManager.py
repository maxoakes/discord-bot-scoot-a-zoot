from discord import FFmpegOpusAudio, FFmpegPCMAudio
from Shared.Util import Util

class MediaManager:

    FFMPEG_PATH = r"A:/Programs/ffmpeg/bin/ffmpeg.exe"
    FFMPEG_OPTS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn -filter:a "volume=0.25"', 'executable': FFMPEG_PATH}
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
    
    async def get_stream_from_url(self, source_string: str, is_opus=False):
        # if it is a local file on this computer
        if source_string.find(Util.FILE_PROTOCOL_PREFIX) > -1:
            return FFmpegPCMAudio(executable=Util.FFMPEG_PATH, source=Util.get_file_location_from_url(source_string))
        else:
            if is_opus:
                return await FFmpegOpusAudio.from_probe(Util.get_youtube_playable_link(source_string), **MediaManager.FFMPEG_OPTS, method='fallback')
            else:
                return FFmpegPCMAudio(source=Util.get_youtube_playable_link(source_string), **MediaManager.FFMPEG_OPTS)