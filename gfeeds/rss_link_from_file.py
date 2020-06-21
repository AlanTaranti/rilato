from gfeeds.rss_parser import parse_feed
from gfeeds.download_manager import extract_feed_url_from_html
from typing import Optional
from os.path import isfile


def get_feed_link_from_str(feed_str: str) -> Optional[str]:
    fp_feed = parse_feed(feed_str)
    if fp_feed is None:
        return None
    self_link = next(
        (link.href for link in fp_feed.feed.links if link.rel == 'self'),
        None
    )
    if self_link is not None and self_link[:4].lower() == 'http':
        return self_link
    entries = fp_feed.get('entries', [])
    if len(entries) <= 0:
        return None
    fp_item_link = entries[0].get('link', None)
    if fp_item_link is None:
        return None
    return extract_feed_url_from_html(fp_item_link)


def get_feed_link_from_file(feed_path: str) -> Optional[str]:
    if not isfile(feed_path):
        return None
    with open(feed_path, 'r') as fd:
        return get_feed_link_from_str(fd.read())
