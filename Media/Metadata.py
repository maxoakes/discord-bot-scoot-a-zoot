class Metadata:
    url: str
    truncated_url: str
    playable_url: str
    title: str
    author: str
    runtime: str
    views: str
    created_at: str
    image_url: str

    def __init__(self, source, info: dict, is_file=False, is_unknown_source=False):
        # attempt to find all the metadata
        self.url = source
        self.playable_url = self.url
        self.truncated_url = self.url.split('//')[-1]
        leading = "" if len(self.truncated_url) <= 55 else "..." 
        self.truncated_url = f"{self.truncated_url[:55]}{leading}" # default fallback title
        self.title = self.truncated_url
        self.author = "Unknown"
        self.runtime = Metadata.seconds_to_string(None)
        self.views = "Unknown"
        self.created_at = "Unknown"
        self.image_url = ""
        
        # if it is a local file, do something way different
        if is_file:
            return
        
        if is_unknown_source:
            self.title = "<Unknown Source>"
            return
        
        try:
            if info.get('formats'):
                self.playable_url = info['formats'][0]['url']
                
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

    # #################################
    # Static functions
    # #################################

    def seconds_to_string(sec) -> str:
        import math
        if sec:
            return f"{math.floor(sec/60)}:{str(math.floor(sec % 60)).zfill(2)}"
        else:
            return "??:??"