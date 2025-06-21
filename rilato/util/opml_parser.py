from functools import reduce
from operator import and_
from pathlib import Path
from gettext import gettext as _
from syndom import Opml
from typing import List, Union


class FeedImportData:
    def __init__(self, feed: str, tags: List[str]):
        self.feed = feed
        self.tags = tags

    def __eq__(self, other) -> bool:
        if not isinstance(other, FeedImportData):
            return False
        return (
            self.feed == other.feed
            and len(self.tags) == len(other.tags)
            and reduce(and_, [t in other.tags for t in self.tags], True)
        )


def opml_to_rss_list(opml_path: Union[str, Path]) -> List[FeedImportData]:
    if isinstance(opml_path, str):
        opml_path = Path(opml_path)
    res = []
    if not opml_path.is_file():
        print(_("Error: OPML path provided does not exist"))
        return res
    try:
        sd_opml = Opml(str(opml_path), True)
        res = [
            FeedImportData(item.get_feed_url(), item.get_categories())
            for item in sd_opml.get_items()
        ]
    except Exception:
        import traceback

        traceback.print_exc()
        print(_("Error parsing OPML file `{0}`").format(opml_path))
    return res  # type: ignore
