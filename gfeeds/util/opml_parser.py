from pathlib import Path
from gettext import gettext as _
from syndom import Opml
from typing import Dict, List, Literal, Union


def opml_to_rss_list(
        opml_path: Union[str, Path]
) -> List[
        Dict[
            Literal['feed', 'tags'],
            Union[str, List[str]]
        ]
]:
    if isinstance(opml_path, str):
        opml_path = Path(opml_path)
    res = []
    if not opml_path.is_file():
        print(_('Error: OPML path provided does not exist'))
        return res
    try:
        sd_opml = Opml(str(opml_path), True)
        res = [
            {'feed': item.get_feed_url(), 'tags': item.get_categories()}
            for item in sd_opml.get_items()
        ]
    except Exception:
        import traceback
        traceback.print_exc()
        print(_('Error parsing OPML file `{0}`').format(opml_path))
    return res  # type: ignore
