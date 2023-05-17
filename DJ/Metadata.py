from Util import Util
from DJ.PlaylistRequest import PlaylistRequest

class Metadata:
    url: str
    truncated_url: str
    title: str
    author: str
    runtime: str
    views: str
    created_at: str
    image_url: str

    def __init__(self, request: PlaylistRequest):
        # attempt to find all the metadata
        self.url = request.get_source_string()
        self.truncated_url = self.url.split('//')[-1]
        leading = "" if len(self.truncated_url) <= 55 else "..." 
        self.truncated_url = f"{self.truncated_url[:55]}{leading}" # default fallback title
        self.title = self.truncated_url
        self.author = "Unknown"
        self.runtime = Metadata.seconds_to_string(None)
        self.views = "Unknown"
        self.created_at = "Unknown"
        self.image_url = ""
        
        import youtube_dl
        youtube = youtube_dl.YoutubeDL(Util.YTDL_OPTIONS)
        try:
            info = youtube.extract_info(self.url, download=False)

            self.title = info.get('title', self.truncated_url)
            self.author = info.get('uploader', self.author) # or 'uploader'?
            self.runtime = Metadata.seconds_to_string(info.get('duration'))

            if info.get('upload_date'):
                import datetime
                timestamp = datetime.date.fromisoformat(info.get('upload_date',"19690101")) #if defaults are used, it is unexpected ytdl behavior
                self.created_at = timestamp.strftime('%A, %b %d, %Y')

            self.image_url = info.get('thumbnail', self.image_url)
            self.title = info.get('track', self.title)
            self.author = info.get('album_artist', self.author)
            self.created_at = info.get('release_year', self.created_at)

            if info.get('view_count'):
                import locale
                locale.setlocale(locale.LC_ALL, 'en_US')
                self.views = locale.format("%d", info.get('view_count', -1), grouping=True) #if defaults are used, it is unexpected ytdl behavior

        except Exception as e:
            print(f"ERROR: Problem getting YTDL info: {e}")


    def seconds_to_string(sec) -> str:
        import math
        if sec:
            return f"{math.floor(sec/60)}:{str(math.floor(sec % 60)).zfill(2)}"
        else:
            return "??:??"