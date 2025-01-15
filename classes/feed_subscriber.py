class FeedSubscriber():

    feed_name: str
    feed_url: str
    subscribing_channels: list[int]
    
    def __init__(self, name, url, channels):
        self.feed_name = name
        self.feed_url = url
        self.subscribing_channels = channels
        if self.subscribing_channels == None:
            self.subscribing_channels = []


    def as_dict(self) -> dict:
        return {
            "feed_name": self.feed_name,
            "feed_url": self.feed_url,
            "subscribing_channels": self.subscribing_channels 
        }