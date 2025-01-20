import datetime
import re
from time import mktime

from state import Utility

class ParsedFeedItem:

    published: datetime.datetime
    title: str
    link: str
    summary: str
    image_urls: list[str]
    video_urls: list[str]

    def __init__(self):
        self.image_urls = []
        self.video_urls = []


class ParsedFeedHeader:

    title: str
    subtitle: str
    link: str
    links: str
    image_url: str
    last_modified: datetime.datetime
    items: list[ParsedFeedItem]

    def __init__(self, feed):
        self.title = feed.feed.get("title", "")
        self.subtitle = feed.feed.get("subtitle", "")
        self.link = feed.feed.get("link", "about:blank")
        self.links = feed.feed.get("links", [])
        self.image_url = None
        if "image" in feed.feed:
            self.image_url = feed.feed.image.get("url", "about:blank")

        self.items = []
        for entry in feed.entries:
            if entry.get("published", None) == None:
                continue
            # with open(f"logs/{self.title}-{datetime.datetime.timestamp(datetime.datetime.now())}.json", "w") as file:
            #     json.dump(entry, file, indent=4)
            item = ParsedFeedItem()
            item.published = datetime.datetime.fromtimestamp(mktime(entry.get("published_parsed")))
            item.published = item.published.replace(tzinfo=datetime.timezone.utc)
            item.title = entry.get("title", "")
            item.link = entry.get("link", "about:blank")
            item.summary = Utility.html_cleanse(entry.get("summary", ""))
            if entry.get("media_content", None) != None:
                for media_object in entry.get("media_content"):
                    if media_object.get("medium", "image") == "image":
                        item.image_urls.append(media_object.get("url", "about:blank"))
                    elif media_object.get("medium") == "video":
                        item.video_urls.append(media_object.get("url", "about:blank"))
            self.items.append(item)
