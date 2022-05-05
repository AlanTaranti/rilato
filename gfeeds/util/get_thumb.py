from urllib.parse import urlparse
from syndom import Html
from gfeeds.util.download_manager import download_raw
from gfeeds.util.sha import shasum
from gfeeds.confManager import ConfManager
from os.path import isfile


confman = ConfManager()


def get_thumb(link):
    dest = str(
        confman.cache_path.joinpath(shasum(link)+'.html')
    )
    try:
        if not isfile(dest):
            download_raw(link, dest)
        sd_html = Html(dest)
    except Exception:
        print('Error parsing HTML')
        return None
    res = sd_html.img_url
    if not res:
        return None
    if res.startswith('https://') or res.startswith('http://'):
        return res
    if res[0] == '/':
        up = urlparse(link)
        res = res.lstrip('/')
        url = f'{up.scheme or "http"}://{up.hostname}/{res}'
        return url
    return f'{link}/{res}'
