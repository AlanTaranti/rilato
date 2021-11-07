import pytz
from datetime import datetime, timezone
from dateutil.parser import parse as dateparse
from dateutil.tz import gettz
from gettext import gettext as _
from gfeeds.download_manager import download_raw
from gfeeds.get_favicon import get_favicon
from os.path import isfile
from gfeeds.confManager import ConfManager
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


class FeedItem:
    def __init__(self, sd_item, parent_feed):
        self.confman = ConfManager()
        self.sd_item = sd_item
        self.title = self.sd_item.get_title()
        self.link = self.sd_item.get_url()
        self.read = self.link in self.confman.read_feeds_items
        self.pub_date_str = self.sd_item.get_pub_date()
        self.pub_date = datetime.now(timezone.utc)  # fallback to avoid errors
        self.parent_feed = parent_feed

        try:
            self.pub_date = dateparse(self.pub_date_str, tzinfos={
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
            if not self.pub_date.tzinfo:
                self.pub_date = pytz.UTC.localize(self.pub_date)
        except Exception:
            print(_(
                'Error: unable to parse datetime {0} for feeditem {1}'
            ).format(self.pub_date_str, self))

        self.image_url = sd_item.get_img_url()
        # sidebar row will try to async get an image from html if above failed

    def set_thumb_from_link(self):
        self.image_url = get_thumb(self.link)

    def set_read(self, read):
        if read == self.read:  # how could this happen?
            return
        if read and self.link not in self.confman.read_feeds_items:
            self.confman.read_feeds_items.append(self.link)
        elif self.link in self.confman.read_feeds_items:
            self.confman.read_feeds_items.remove(self.link)
        self.read = read

    def __repr__(self):
        return 'FeedItem Object `{0}` from Feed {1}'.format(
            self.title,
            self.parent_feed.title
        )


class Feed:
    def __init__(self, download_res, no_preprocessing: bool = False):
        self.is_null = False
        self.error = None
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
            print("Error parsing feed")
            import traceback
            traceback.print_exc()
        # with open(feedpath, 'r') as fd:
        #     feed_str = fd.read()
        # self.fp_feed = parse_feed(feed_str, no_preprocessing)
        if self.sd_feed is None:
            self.is_null = True
            self.error = _('Errors while parsing feed `{0}`').format(
                feedpath
            )
            return
        self.rss_link = download_res[1] or self.sd_feed.get_rss_url()

        self.confman = ConfManager()
        self.init_time = pytz.UTC.localize(datetime.utcnow())
        self.title = self.sd_feed.get_title()
        self.link = self.sd_feed.get_url()
        self.description = self.sd_feed.get_description()
        self.image_url = self.sd_feed.get_img_url()
        self.items = []
        raw_entries = self.sd_feed.get_items()
        for entry in raw_entries:
            n_item = FeedItem(entry, self)
            item_age = self.init_time - n_item.pub_date
            if item_age < self.confman.max_article_age:
                self.items.append(n_item)
            elif n_item.read:
                self.confman.read_feeds_items.remove(n_item.link)

        if (
                not self.title and
                len(raw_entries) == 0
        ):
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

    def __repr__(self):
        return f'Feed Object `{self.title}`; {len(self.items)} items'
