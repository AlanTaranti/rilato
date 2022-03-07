from pathlib import Path
from typing import Optional, Tuple, Union
import pytz
from gi.repository import GObject, GLib
from datetime import datetime, timezone
from dateutil.parser import parse as dateparse
from dateutil.tz import gettz
from gettext import gettext as _
from gfeeds.download_manager import download_raw
from gfeeds.get_favicon import get_favicon
from os.path import isfile
from gfeeds.confManager import ConfManager
from gfeeds.tag_store import TagStore
from gfeeds.sha import shasum
# from bs4 import UnicodeDammit  # TODO: reimplement it!
from gfeeds.get_thumb import get_thumb
from syndom import Feed as SynDomFeed


def get_encoding(in_str):
    sample = in_str[:200]
    if 'encoding' in sample:
        enc_i = sample.index('encoding')
        trim = sample[enc_i+10:]
        str_delimiter = "'" if "'" in trim else '"'
        encoding = trim[:trim.index(str_delimiter)]
        return encoding
    return 'utf-8'


class FeedItem(GObject.Object):
    __gsignals__ = {
        'changed': (
            GObject.SignalFlags.RUN_FIRST, None, (str,)
        )
    }

    def __init__(self, sd_item, parent_feed):
        self.confman = ConfManager()
        self.sd_item = sd_item
        self.__title = self.sd_item.get_title()
        self.__link = self.sd_item.get_url()
        self.pub_date_str = self.sd_item.get_pub_date()
        # fallback to avoid errors
        self.__pub_date = datetime.now(timezone.utc)
        self.parent_feed = parent_feed

        # used to identify article for read/unread and thumbs cache
        self.identifier = self.__link or (self.__title + self.pub_date_str)
        self.__read = self.identifier in self.confman.read_feeds_items

        try:
            self.__pub_date = dateparse(self.pub_date_str, tzinfos={
                'UT': gettz('GMT'),
                'EST': -18000,
                'EDT': -14400,
                'CST': -21600,
                'CDT': -18000,
                'MST': -25200,
                'MDT': -21600,
                'PST': -28800,
                'PDT': -25200
            })
            if not self.__pub_date.tzinfo:
                self.__pub_date = pytz.UTC.localize(self.__pub_date)
        except Exception:
            print(_(
                'Error: unable to parse datetime {0} for feeditem {1}'
            ).format(self.pub_date_str, self))

        self.__image_url = sd_item.get_img_url()
        # sidebar row will try to async get an image from html if above failed
        super().__init__()

    @GObject.Property(type=str)
    def title(self) -> str:
        return self.__title

    @GObject.Property()
    def pub_date(self) -> datetime:
        return self.__pub_date

    @GObject.Property(type=str)
    def link(self) -> str:
        return self.__link

    @GObject.Property(type=bool, default=False)
    def read(self) -> bool:
        return self.__read

    @read.setter
    def read(self, n_read: bool):
        self.__set_read(n_read)

    @GObject.Property(type=str)
    def image_url(self) -> str:
        return self.__image_url

    @image_url.setter
    def image_url(self, n_image_url: str):
        self.__image_url = n_image_url

    def set_thumb_from_link(self):
        image_url = get_thumb(self.__link)

        def cb(url):
            self.image_url = url

        GLib.idle_add(cb, image_url)

    def __set_read(self, read):
        if read == self.__read:
            return
        self.parent_feed.unread_count += -1 if read else 1
        if read and self.identifier not in self.confman.read_feeds_items:
            self.confman.read_feeds_items.append(self.identifier)
        elif not read and self.identifier in self.confman.read_feeds_items:
            self.confman.read_feeds_items.remove(self.identifier)
        self.__read = read

    def __repr__(self):
        return 'FeedItem Object `{0}` from Feed {1}'.format(
            self.__title,
            self.parent_feed.title
        )


class FeedParser(GObject.Object):

    def __init__(self):
        super().__init__()
        self.is_null = False
        self.error = None
        self.confman = ConfManager()

    def parse(
            self, download_res: Tuple[Union[str, Path, bool], Optional[str]]
    ):
        if download_res[0] is False:  # indicates failed download
            self.is_null = True
            self.error = download_res[1]
            print(download_res)
            return
        feedpath = download_res[0]
        try:
            self.sd_feed = SynDomFeed(str(feedpath))
        except Exception:
            self.sd_feed = None
            print('Error parsing feed (caught). Traceback:')
            import traceback
            traceback.print_exc()
        if self.sd_feed is None:
            self.is_null = True
            self.error = _('Errors while parsing feed `{0}`').format(
                feedpath
            )
            return
        self.rss_link = download_res[1] or self.sd_feed.get_rss_url()

        self.confman = ConfManager()
        self.title = self.sd_feed.get_title()
        self.link = self.sd_feed.get_url()
        self.description = self.sd_feed.get_description()
        self.image_url = self.sd_feed.get_img_url()
        self.feed_identifier = self.rss_link+self.title
        self.raw_entries = self.sd_feed.get_items()
        if not self.title and len(self.raw_entries) == 0:
            # if these conditions are met, there's reason to believe
            # this is not an rss/atom feed
            self.is_null = True
            self.error = _(
                '`{0}` may not be an RSS or Atom feed'
            ).format(self.rss_link)
            return

        if not self.title:
            self.title = self.link or self.rss_link

        self.favicon_path = str(self.confman.thumbs_cache_path.joinpath(
            shasum(self.rss_link)+'.png'
        ))
        if not isfile(self.favicon_path):
            if self.image_url:
                try:
                    download_raw(self.image_url, self.favicon_path)
                except Exception:
                    print('Invalid image url for feed `{0}` ({1})'.format(
                        self.rss_link, self.image_url
                    ))
                    self.image_url = None
            if not self.image_url:
                try:
                    get_favicon(self.rss_link, self.favicon_path)
                    if not isfile(self.favicon_path):
                        get_favicon(
                            self.link or self.items[0].link,
                            self.favicon_path
                        )
                except Exception:
                    print(f'No favicon for feed `{self.rss_link}`')
                    self.favicon_path = None


class Feed(GObject.Object):
    __gsignals__ = {
        'empty_changed': (
            GObject.SignalFlags.RUN_FIRST, GObject.TYPE_NONE, ()
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
                self.confman.read_feeds_items.remove(n_item.identifier)

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
    def image_url(self) -> str:
        return self.__image_url

    @image_url.setter
    def image_url(self, n_image_url: str):
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
