from pathlib import Path
from typing import Optional
from gettext import gettext as _
from gfeeds.util.get_favicon import get_favicon
from os.path import isfile
from gfeeds.confManager import ConfManager
from gfeeds.util.sha import shasum
# from bs4 import UnicodeDammit  # TODO: reimplement it!
from syndom import Feed as SynDomFeed


class FeedParser:
    def __init__(self):
        super().__init__()
        self.is_null = False
        self.error = None
        self.confman = ConfManager()

    def parse(
        self, feedpath: Optional[Path] = None, rss_link: Optional[str] = None,
        failed: bool = False, error: Optional[str] = None
    ):
        if failed:  # indicates failed download
            self.is_null = True
            self.error = error or '<NULL ERROR>'
            print(error)
            return
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
        self.rss_link = rss_link or self.sd_feed.get_rss_url()

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
            shasum(self.rss_link+'v2')+'.png'
        ))
        if not isfile(self.favicon_path):
            if self.image_url:
                try:
                    get_favicon(self.image_url, self.favicon_path, direct=True)
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
                            self.link or self.raw_entries[0].uri,
                            self.favicon_path
                        )
                except Exception:
                    print(f'No favicon for feed `{self.rss_link}`')
                    self.favicon_path = None
