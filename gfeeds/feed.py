from typing import List, Optional
from gi.repository import GObject, GLib
from datetime import datetime
from gfeeds.confManager import ConfManager
from gfeeds.feed_item import FeedItem
import pytz
import gfeeds.feeds_manager as feeds_manager
from syndom import Feed as SynDomFeed, FeedItem as SynDomFeedItem


class Feed(GObject.Object):
    __gsignals__ = {
        'empty_changed': (
            GObject.SignalFlags.RUN_FIRST, None, ()
        )
    }

    __title = ''
    __link = ''
    __description = ''
    __image_url = ''
    __unread_count = 0
    rss_link = ''
    tags = list()
    items = dict()
    sd_feed = None
    favicon_path = ''
    init_time = None

    def __init__(
        self, rss_link: str, title: str, link: str, description: str,
        image_url: Optional[str], favicon_path: Optional[str],
        sd_feed: SynDomFeed, raw_entries: List[SynDomFeedItem]
    ):
        super().__init__()
        self.confman = ConfManager()
        self.feedman = feeds_manager.FeedsManager()
        self.tag_store = self.feedman.tag_store
        self.__unread_count = 0
        self.tags = list()
        self.items = dict()
        self.update(
            rss_link, title, link, description, image_url, favicon_path,
            sd_feed, raw_entries
        )

    def update(
        self, rss_link: str, title: str, link: str, description: str,
        image_url: Optional[str], favicon_path: Optional[str],
        sd_feed: SynDomFeed, raw_entries: List[SynDomFeedItem]
    ):
        self.rss_link = rss_link
        self.__title = title
        self.__link = link
        self.__description = description
        self.__image_url = image_url
        self.favicon_path = favicon_path
        self.sd_feed = sd_feed

        unread_count = 0
        self.init_time = pytz.UTC.localize(datetime.utcnow())
        for entry in raw_entries:
            n_item = FeedItem(entry, self)
            uid = self.rss_link + n_item.identifier
            item_age = self.init_time - n_item.pub_date  # type: ignore
            valid_age = item_age <= self.confman.max_article_age
            if uid in self.items:
                if not valid_age:
                    del self.items[uid]
            else:
                if valid_age:
                    self.items[uid] = n_item

            if valid_age and not n_item.read:
                unread_count += 1
            if not valid_age and n_item.read:
                read_items: List[str] = self.confman.conf['read_items']
                read_items.remove(n_item.identifier)
                self.confman.conf['read_items'] = read_items

        if self.rss_link in self.confman.conf['feeds']:
            feed_conf = (self.get_conf_dict() or dict())
            for tag_name in feed_conf.get('tags', []):
                tag_obj = self.tag_store.get_tag(tag_name)
                if tag_obj is not None and tag_obj not in self.tags:
                    self.tags.append(tag_obj)

        # Set property, trigger signal (avoiding excess signals during init)
        if unread_count != self.__unread_count:
            def do():
                self.unread_count = unread_count
            GLib.idle_add(do)

    def get_conf_dict(self) -> Optional[dict]:
        return self.confman.conf['feeds'].get(self.rss_link, None)

    @GObject.Property(type=str)
    def title(self) -> str:  # type: ignore
        return self.__title

    @GObject.Property(type=str)
    def link(self) -> str:  # type: ignore
        return self.__link

    @GObject.Property(type=str)
    def description(self) -> str:  # type: ignore
        return self.__description

    @GObject.Property(type=str)
    def image_url(self) -> Optional[str]:  # type: ignore
        return self.__image_url

    @image_url.setter
    def image_url(self, n_image_url: Optional[str]):
        self.__image_url = n_image_url

    @GObject.Property(type=int, default=0)
    def unread_count(self) -> int:  # type: ignore
        return self.__unread_count

    @unread_count.setter
    def unread_count(self, v: int):
        prev = self.__unread_count
        self.__unread_count = v
        if self.__unread_count == 0 and prev > 0:
            self.emit('empty_changed')
        elif self.__unread_count > 0 and prev == 0:
            self.emit('empty_changed')

        change = self.__unread_count - prev
        for tag in self.tags:
            tag.increment_unread_count(change)

    def __repr__(self):
        return f'Feed Object `{self.__title}`; {len(self.items)} items'
