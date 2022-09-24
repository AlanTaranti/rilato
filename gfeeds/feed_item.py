from gettext import gettext as _
from typing import TYPE_CHECKING, List, Optional
from bs4 import BeautifulSoup
from gi.repository import GObject, GLib
from dateutil.tz import gettz
from datetime import datetime, timezone
from dateutil.parser import parse as dateparse
from gfeeds.util.get_thumb import get_thumb
from gfeeds.confManager import ConfManager
import pytz
if TYPE_CHECKING:
    from gfeeds.feed import Feed


class FeedItem(GObject.Object):
    __gsignals__ = {
        'changed': (
            GObject.SignalFlags.RUN_FIRST, None, (str,)
        )
    }

    def __init__(self, sd_item, parent_feed: 'Feed'):
        self.confman = ConfManager()
        self.parent_feed = parent_feed
        self.sd_item = sd_item
        title = self.sd_item.get_title()
        self.__title = (
            BeautifulSoup(title, features='lxml').text
            if title and '</' in title
            else title
        )
        self.__link = self.sd_item.get_url()
        self.pub_date_str = self.sd_item.get_pub_date()
        # fallback to avoid errors
        self.__pub_date = datetime.now(timezone.utc)

        # used to identify article for read/unread and thumbs cache
        self.identifier = self.__link or (self.__title + self.pub_date_str)
        self.__read = self.identifier in self.confman.conf['read_items']

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
    def title(self) -> str:  # type: ignore
        return self.__title

    @GObject.Property()
    def pub_date(self) -> datetime:  # type: ignore
        return self.__pub_date

    @GObject.Property(type=str)
    def link(self) -> str:  # type: ignore
        return self.__link

    @GObject.Property(type=bool, default=False)
    def read(self) -> bool:  # type: ignore
        return self.__read

    @read.setter
    def read(self, n_read: bool):
        self.__set_read(n_read)

    @GObject.Property(type=str)
    def image_url(self) -> str:  # type: ignore
        return self.__image_url

    @image_url.setter
    def image_url(self, n_image_url: str):
        self.__image_url = n_image_url

    def set_thumb_from_link(self) -> Optional[str]:
        image_url = get_thumb(self.__link)

        def cb(url):
            self.image_url = url

        GLib.idle_add(cb, image_url)
        return image_url

    def __set_read(self, read):
        if read == self.__read:
            return
        self.parent_feed.unread_count += -1 if read else 1
        read_items: List[str] = self.confman.conf['read_items']
        if read and self.identifier not in read_items:
            read_items.append(self.identifier)
        elif not read and self.identifier in read_items:
            read_items.remove(self.identifier)
        self.confman.conf['read_items'] = read_items
        self.__read = read

    def __repr__(self):
        return 'FeedItem Object `{0}` from Feed {1}'.format(
            self.__title,
            self.parent_feed.title
        )
