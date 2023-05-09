from discord import FFmpegOpusAudio, FFmpegPCMAudio, channel

from Util import Util

class MediaManager:
    FFMPEG_OPTS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn -filter:a "volume=0.25"', 'executable': Util.FFMPEG_PATH}
    YTDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist':'True', 'quiet':'True'}

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
    
    async def get_best_stream_from_url(self, source_string: str):
        stream = None
        metadata = ""
        if source_string.find("https://youtu.be/") > -1 or source_string.find("https://www.youtube.com/watch?") > -1:
            print("\tFound a youtube source")
            import youtube_dl
            youtube = youtube_dl.YoutubeDL(MediaManager.YTDL_OPTIONS)
            info = youtube.extract_info(source_string, download=False)
            # print(info['formats'][0]['url'])
            stream = FFmpegPCMAudio(info['formats'][0]['url'], **MediaManager.FFMPEG_OPTS)
            metadata = info.get('title', "_unknown")
        else:
            print("\tFound a different source")
            stream = await FFmpegOpusAudio.from_probe(source_string, **MediaManager.FFMPEG_OPTS, method='fallback')
            metadata = source_string
        return (stream, metadata)