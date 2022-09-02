from pathlib import Path
from typing import List, Optional
from gettext import gettext as _
from gfeeds.util.get_favicon import get_favicon
from os.path import isfile
from gfeeds.util.paths import THUMBS_CACHE_PATH
from gfeeds.util.sha import shasum
# from bs4 import UnicodeDammit  # TODO: reimplement it!
from syndom import Feed as SynDomFeed, FeedItem as SynDomFeedItem


class FeedParserRes:
    def __init__(
        self,
        is_null: bool = False,
        error: Optional[str] = None,
        sd_feed: SynDomFeed = None,
        rss_link: Optional[str] = None,
        title: Optional[str] = None,
        link: Optional[str] = None,
        description: Optional[str] = None,
        image_url: Optional[str] = None,
        favicon_path: Optional[str] = None,
        raw_entries: List[SynDomFeedItem] = []
    ):
        self.is_null = is_null
        self.error = error
        self.sd_feed = sd_feed
        self.rss_link = rss_link or ''
        self.title = title or ''
        self.link = link or ''
        self.description = description or ''
        self.image_url = image_url
        self.favicon_path = favicon_path
        self.raw_entries = raw_entries

    @property
    def feed_identifier(self) -> str:
        assert self.rss_link
        assert self.title
        return self.rss_link + self.title


def parse_feed(
        feedpath: Optional[Path],
        rss_link_: Optional[str] = None,
        failed: bool = False,
        error: Optional[str] = None
) -> FeedParserRes:
    if failed:
        print(error)
        return FeedParserRes(is_null=True, error=(error or '<NULL ERROR>'))
    sd_feed = None
    try:
        sd_feed = SynDomFeed(str(feedpath))
    except Exception:
        print('Error parsing feed (caught); will try extracting from HTML')
    if sd_feed is None:
        return FeedParserRes(
            is_null=True, error=_(
                'Errors while parsing feed `{0}`, URL: `{1}`'
            ).format(feedpath, rss_link_)
        )
    title = sd_feed.get_title()
    raw_entries = sd_feed.get_items()
    if not title and len(raw_entries) == 0:
        # if these conditions are met, there's reason to believe
        # this is not an rss/atom feed
        return FeedParserRes(
            is_null=False, error=_(
                '`{0}` may not be an RSS or Atom feed'
            ).format(rss_link_)
        )
    link = sd_feed.get_url()
    rss_link = rss_link_ or sd_feed.get_rss_url()
    if not title:
        title = rss_link
    favicon_path = str(THUMBS_CACHE_PATH.joinpath(
        shasum(rss_link+'v2')+'.png'
    ))
    image_url = sd_feed.get_img_url()
    if not isfile(favicon_path):
        if image_url:
            try:
                get_favicon(image_url, favicon_path, direct=True)
            except Exception:
                print('Invalid image url for feed `{0}` ({1})'.format(
                    rss_link, image_url
                ))
                image_url = None
        if not image_url:
            try:
                get_favicon(rss_link, favicon_path)
                if not isfile(favicon_path):
                    get_favicon(
                        link or raw_entries[0].uri,
                        favicon_path
                    )
            except Exception:
                print(f'No favicon for feed `{rss_link}`')
                favicon_path = None
    return FeedParserRes(
        is_null=False, error=None, sd_feed=sd_feed,
        rss_link=rss_link,
        title=title,
        link=link,
        description=sd_feed.get_description(),
        image_url=image_url,
        favicon_path=favicon_path,
        raw_entries=raw_entries
    )
