class RadioStation():
    name: str
    display_name: str
    url: str
    is_opus: bool

    def __init__(self, name: str, display_name: str, url: str, is_opus=True):
        self.name = name
        self.display_name = display_name
        self.url = url
        self.is_opus = is_opus


    def as_dict(self):
        return {
            "name": self.name,
            "display_name": self.display_name,
            "url": self.url,
            "is_opus": self.is_opus
        }