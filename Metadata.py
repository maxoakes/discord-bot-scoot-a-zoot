import datetime
from Util import Util
from PlaylistRequest import PlaylistRequest

class Metadata:
    url: str
    title: str
    author: str
    runtime: str
    views: str
    created_at: str
    image_url: str

    def __init__(self, request: PlaylistRequest):
        # attempt to find all the metadata
        self.url = request.get_source_string()
        self.title = None
        self.author = None
        self.runtime = None
        self.views = None
        self.created_at = None
        self.image_url = None

        if self.url.find(Util.YOUTUBE_URL_PREFIX_FULL) > -1 or self.url.find(Util.YOUTUBE_URL_PREFIX_SHORT) > -1:
            import locale
            locale.setlocale(locale.LC_ALL, 'en_US')
            
            import youtube_dl
            youtube = youtube_dl.YoutubeDL(Util.YTDL_OPTIONS)
            info = youtube.extract_info(self.url, download=False)

            self.title = info.get('title')
            self.author = info.get('uploader') # or 'uploader'?
            self.runtime = Metadata.seconds_to_string(info.get('duration'))
            self.views = locale.format("%d", info.get('view_count'), grouping=True)
            timestamp = datetime.date.fromisoformat(info.get('upload_date'))
            self.created_at = timestamp.strftime('%A, %b %d, %Y')
            self.image_url = info.get('thumbnail')
            self.title = info.get('track') if info.get('track') else self.title
            self.author = info.get('album_artist') if info.get('album_artist') else self.author
            self.created_at = info.get('release_year') if info.get('release_year') else self.created_at
        else:
            title = self.url.split('//')[-1]
            leading = "" if len(title) <= 40 else "..." 
            self.title = f"{title[:40]}{leading}"
            self.author = "Unknown"
            self.runtime = Metadata.seconds_to_string(None)
            self.views = "Unknown"
            self.created_at = "Unknown"

    def seconds_to_string(sec) -> str:
        import math
        if sec:
            return f"{math.floor(sec/60)}:{str(sec % 60).zfill(2)}"
        else:
            return "??:??"