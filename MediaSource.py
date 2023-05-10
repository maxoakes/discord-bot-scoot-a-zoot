class MediaSource:
    __source_url: str
    __is_video: bool

    def __init__(self, url, is_video=False):
        self.__source_url = url
        self.__is_video = is_video

    def get_url(self):
        return self.__source_url
    
    def is_video(self):
        return self.__is_video
