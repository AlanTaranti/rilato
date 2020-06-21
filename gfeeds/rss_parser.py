import json
import feedparser
import pytz
from datetime import datetime, timezone
from dateutil.parser import parse as dateparse
from dateutil.tz import gettz
from gettext import gettext as _
from gfeeds.download_manager import download_raw
from gfeeds.get_favicon import get_favicon
from os.path import isfile
from os import remove
from gfeeds.confManager import ConfManager
from gfeeds.sha import shasum
from PIL import Image
from bs4 import UnicodeDammit
from typing import Optional


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
    def __init__(self, fp_item, parent_feed):
        self.confman = ConfManager()
        self.fp_item = fp_item
        self.is_saved = 'linkhash' in self.fp_item.keys()
        self.title = self.fp_item.get('title', '')
        self.link = self.fp_item.get('link', '')
        self.read = self.link in self.confman.read_feeds_items
        # self.description = self.fp_item.get('description', '')
        self.pub_date_str = self.fp_item.get(
            'published',
            self.fp_item.get('updated', '')
        )
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

    def to_dict(self):
        return {
            'title': self.title,
            'link': self.link,
            'linkhash': shasum(self.link),
            'published': str(self.pub_date),
            'parent_feed': {
                'title': self.parent_feed.title,
                'link': self.parent_feed.link,
                'favicon_path': self.parent_feed.favicon_path
            }
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def new_from_dict(cls, n_fi_dict):
        return cls(
            n_fi_dict,
            FakeFeed(n_fi_dict['parent_feed'])
        )

    @classmethod
    def new_from_json(cls, fi_json):
        return cls.new_from_dict(json.loads(fi_json))


class FakeFeed:
    def __init__(self, f_dict):
        self.title = f_dict.get('title', '')
        self.link = f_dict.get('link', '')
        self.favicon_path = f_dict.get('favicon_path', '')
        if isfile(self.favicon_path):
            favicon = Image.open(self.favicon_path)
            if favicon.width != 32:
                favicon = favicon.resize((32, 32), Image.BILINEAR)
                favicon.save(self.favicon_path, 'PNG')
            favicon.close()

    def __repr__(self):
        return f'FakeFeed Object `{self.title}`'


def parse_feed(feed_str: str, no_preprocessing=False) -> Optional[str]:
    if no_preprocessing:
        return feedparser.parse(feed_str)
    udammit = UnicodeDammit(feed_str)
    feed_str = udammit.unicode_markup
    feed_str = feed_str.replace(
        get_encoding(feed_str),
        'utf-8'
    )
    forbidden_namespaces = [
        'atom',
        'openSearch',
        'thr'
    ]
    for fns in forbidden_namespaces:
        feed_str = feed_str.replace(
            f'<{fns}:', '<'
        )
        feed_str = feed_str.replace(
            f'</{fns}:', '</'
        )
    try:
        fp_feed = feedparser.parse(feed_str)
        return fp_feed
    except Exception:
        import traceback
        traceback.print_exc()
        return None


class Feed:
    def __init__(self, download_res, no_preprocessing=False):
        self.is_null = False
        self.error = None
        if download_res[0] is False:  # indicates failed download
            self.is_null = True
            self.error = download_res[1]
            print(download_res)
            return
        feedpath = download_res[0]
        self.rss_link = download_res[1]
        with open(feedpath, 'r') as fd:
            feed_str = fd.read()
        self.fp_feed = parse_feed(feed_str, no_preprocessing)
        if self.fp_feed is None:
            self.is_null = True
            self.error = _('Errors while parsing feed `{0}`').format(
                self.rss_link
            )
            return

        self.confman = ConfManager()
        self.init_time = pytz.UTC.localize(datetime.utcnow())

        self.fp_feed['feed'] = self.fp_feed.get(
            'feed',
            self.fp_feed.get('channel', {})
        )
        self.title = self.fp_feed.feed.get('title', '')
        self.link = self.fp_feed.feed.get('link', '')
        self.description = self.fp_feed.feed.get('subtitle', self.link)
        # self.language = self.fp_feed.get('', '')
        image_tag = self.fp_feed.get('feed', {}).get('image', {})
        self.image_url = image_tag.get(
            'href',
            image_tag.get('url', '')
        )
        self.items = []
        raw_entries = self.fp_feed.get('entries', [])
        for entry in raw_entries:
            n_item = FeedItem(entry, self)
            item_age = self.init_time - n_item.pub_date
            if item_age < self.confman.max_article_age:
                self.items.append(n_item)
            elif n_item.read:
                self.confman.read_feeds_items.remove(n_item.link)
        self.color = [0.0, 0.0, 0.0]

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
            if not no_preprocessing:
                self.__init__(download_res, no_preprocessing=True)
            return

        if not self.title:
            self.title = self.link
            if not self.title:
                self.title = self.rss_link

        self.favicon_path = self.confman.thumbs_cache_path+'/' + \
            shasum(self.link)+'.png'
        if not isfile(self.favicon_path):
            if self.image_url:
                try:
                    download_raw(self.image_url, self.favicon_path)
                except Exception:
                    self.image_url = None
            if not self.image_url:
                try:
                    get_favicon(self.link, self.favicon_path)
                    if not isfile(self.favicon_path):
                        get_favicon(self.items[0].link, self.favicon_path)
                except Exception:
                    print('No favicon')
        if isfile(self.favicon_path):
            try:
                self._resize_favicon(self.favicon_path)
            except Exception:
                print(_(
                    'Error resizing favicon for feed {0}. '
                    'Probably not an image.\n'
                    'Trying downloading favicon from an article.'
                ).format(self.title))
                try:
                    get_favicon(self.items[0].link, self.favicon_path)
                    self._resize_favicon(self.favicon_path)
                except Exception:
                    print(_(
                        'Error resizing favicon from article for feed {0}.\n'
                        'Deleting invalid favicon.'
                    ).format(self.title))
                    remove(self.favicon_path)

    def _resize_favicon(self, img_path):
        favicon = Image.open(img_path)
        if favicon.width != 32:
            favicon = favicon.resize((32, 32), Image.BILINEAR)
            favicon.save(self.favicon_path, 'PNG')
        favicon.close()

    def __repr__(self):
        return f'Feed Object `{self.title}`; {len(self.items)} items'
