import os
import asyncio
from dotenv import load_dotenv
from discord import FFmpegOpusAudio, FFmpegPCMAudio
from Util import Util

class MediaManager:

    # final
    FFMPEG_OPTS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn -filter:a "volume=0.33"'}

    # public
    media_loop = None

    # private
    __voice_client = None
    __current_voice_channel = None
    __is_active = False

    def __init__(self):
        load_dotenv()
        self.media_loop = asyncio.get_event_loop()

    def set_voice_client(self, voice_client):
        self.__voice_client = voice_client

    def get_voice_client(self):
        return self.__voice_client
    
    def get_voice_channel(self):
        return self.__current_voice_channel
    
    def get_current_voice_guild(self):
        return self.__voice_client.guild
    
    def set_voice_channel(self, channel):
        self.__current_voice_channel = channel

    def set_active(self, a: bool):
        self.__is_active = a

    def get_active(self):
        return self.__is_active

    async def get_stream_from_url(self, source_string: str, is_opus=False):
        # if it is a local file on this computer
        if source_string.find(Util.FILE_PROTOCOL_PREFIX) == 0:
            return FFmpegPCMAudio(executable=os.getenv('FFMPEG_PATH'), source=source_string[len(Util.FILE_PROTOCOL_PREFIX):])
        else:
            if is_opus:
                return await FFmpegOpusAudio.from_probe(source_string, executable=os.getenv('FFMPEG_PATH'), **MediaManager.FFMPEG_OPTS, method='fallback')
            else:
                return FFmpegPCMAudio(source=source_string, executable=os.getenv('FFMPEG_PATH'), **MediaManager.FFMPEG_OPTS)
