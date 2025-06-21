from rilato.util.download_manager import extract_feed_url_from_html
from typing import Optional
from os.path import isfile
from syndom import Feed as SynDomFeed


def get_feed_link_from_file(feed_path: str) -> Optional[str]:
    if not isfile(feed_path):
        return None
    try:
        sd_feed = SynDomFeed(str(feed_path))
    except Exception:
        import traceback

        traceback.print_exc()
        print(f"Error parsing feed `{feed_path}`")
        return None
    res = sd_feed.get_rss_url()
    if res:
        return res
    url = sd_feed.get_url()
    if url:
        return extract_feed_url_from_html(url)
    items = sd_feed.get_items()
    if len(items) <= 0:
        return None
    item_url = items[0].get_url()
    if item_url:
        return extract_feed_url_from_html(item_url)
    return None
