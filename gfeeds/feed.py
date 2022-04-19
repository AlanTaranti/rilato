from typing import Optional
from gi.repository import GObject, GLib
from datetime import datetime
from gfeeds.feed_parser import FeedParser
from gfeeds.tag_store import TagStore
from gfeeds.confManager import ConfManager
from gfeeds.feed_item import FeedItem
import pytz


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

    def __init__(self, tag_store: TagStore):
        super().__init__()
        self.confman = ConfManager()
        self.tag_store = tag_store
        self.__unread_count = 0
        self.tags = []
        self.items = {}

    def populate(self, parser: FeedParser):
        self.rss_link = parser.rss_link
        self.__title = parser.title
        self.__link = parser.link
        self.__description = parser.description
        self.__image_url = parser.image_url
        self.favicon_path = parser.favicon_path
        self.sd_feed = parser.sd_feed

        unread_count = 0
        self.init_time = pytz.UTC.localize(datetime.utcnow())
        for entry in parser.raw_entries:
            n_item = FeedItem(entry, self)
            uid = self.rss_link + n_item.identifier
            item_age = self.init_time - n_item.pub_date
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
                self.confman.conf['read_items'].remove(n_item.identifier)
                self.confman.save_conf()

        if self.rss_link in self.confman.conf['feeds']:
            feed_conf = self.confman.conf['feeds'][self.rss_link]
            if 'tags' in feed_conf:
                for tag_name in feed_conf['tags']:
                    tag_obj = self.tag_store.get_tag(tag_name)
                    if tag_obj is not None and tag_obj not in self.tags:
                        self.tags.append(tag_obj)

        # Set property, trigger signal (avoiding excess signals during init)
        if unread_count != self.__unread_count:
            def do():
                self.unread_count = unread_count
            GLib.idle_add(do)

    @GObject.Property(type=str)
    def title(self) -> str:
        return self.__title

    @GObject.Property(type=str)
    def link(self) -> str:
        return self.__link

    @GObject.Property(type=str)
    def description(self) -> str:
        return self.__description

    @GObject.Property(type=str)
    def image_url(self) -> Optional[str]:
        return self.__image_url

    @image_url.setter
    def image_url(self, n_image_url: Optional[str]):
        self.__image_url = n_image_url

    @GObject.Property(type=int, default=0)
    def unread_count(self) -> int:
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
