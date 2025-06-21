from syndom import Html
from rilato.util.create_full_url import create_full_url
from rilato.util.download_manager import download_raw
from rilato.util.paths import CACHE_PATH
from rilato.util.sha import shasum
from os.path import isfile


def get_thumb(link):
    dest = str(CACHE_PATH.joinpath(shasum(link) + ".html"))
    try:
        if not isfile(dest):
            download_raw(link, dest)
        sd_html = Html(dest)
    except Exception:
        print("Error parsing HTML")
        return None
    res = sd_html.img_url
    if not res:
        return None
    return create_full_url(link, res)
