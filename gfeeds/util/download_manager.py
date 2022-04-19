from gettext import gettext as _
from os.path import isfile
from pathlib import Path
import requests
from gfeeds.confManager import ConfManager
from gfeeds.util.sha import shasum
from syndom import Html
from typing import Optional, Tuple, Union

confman = ConfManager()

GET_HEADERS = {
    'User-Agent': 'gfeeds/1.0',
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate'
}

TIMEOUT = 30


class DownloadError(Exception):
    def __init__(self, code, *args):
        self.download_error_code = code


# will return the content of a file if it's a file url
def download_text(link: str) -> str:
    if link[:8] == 'file:///':
        with open(link[7:]) as fd:
            toret = fd.read()
        return toret
    res = requests.get(link, headers=GET_HEADERS, timeout=TIMEOUT)
    if 200 <= res.status_code <= 299:
        res.encoding = 'utf-8'
        return res.text  # TODO: this can break weird encodings!
    else:
        raise DownloadError(
            res.status_code, f'response code {res.status_code}'
        )


def download_raw(link: str, dest: str) -> None:
    res = requests.get(link, headers=GET_HEADERS, timeout=TIMEOUT)
    if res.status_code == 200:
        with open(dest, 'wb') as fd:
            for chunk in res.iter_content(1024):
                fd.write(chunk)
    else:
        raise requests.HTTPError(
            f'response code {res.status_code} for url `{link}`'
        )


def extract_feed_url_from_html(link: str) -> Optional[str]:
    dest = str(
        confman.cache_path.joinpath(shasum(link)+'.html')
    )
    try:
        if not isfile(dest):
            download_raw(link, dest)
        sd_html = Html(dest)
        return sd_html.rss_url or None
        # maybe sanitize(sd_html.rss_url) ?
    except Exception:
        print('Error extracting feed from HTML')
    return None


def download_feed(
        link: str, get_cached: bool = False
) -> dict:
    dest_path = confman.cache_path.joinpath(shasum(link)+'.rss')
    if get_cached:
        return {
            'feedpath': dest_path if isfile(dest_path) else 'not_cached',
            'rss_link': link,
            'failed': not isfile(dest_path),
            'error': None
        }
    headers = GET_HEADERS.copy()
    if (
            'last-modified' in confman.conf['feeds'][link].keys() and
            isfile(dest_path)
    ):
        headers['If-Modified-Since'] = \
            confman.conf['feeds'][link]['last-modified']
    try:
        res = requests.get(
            link, headers=headers, allow_redirects=True, timeout=TIMEOUT
        )
    except requests.exceptions.ConnectTimeout:
        return {
            'feedpath': None,
            'rss_link': link,
            'failed': True,
            'error': _('`{0}`: connection timed out').format(link)
        }
    except Exception:
        import traceback
        traceback.print_exc()
        return {
            'feedpath': None,
            'rss_link': link,
            'failed': True,
            'error': _('`{0}` might not be a valid address').format(link)
        }
    if 'last-modified' in res.headers.keys():
        confman.conf['feeds'][link]['last-modified'] = \
            res.headers['last-modified']

    def handle_200():
        if (
                'last-modified' not in res.headers.keys() and
                'last-modified' in confman.conf['feeds'][link].keys()
        ):
            confman.conf['feeds'][link].pop('last-modified')
        with open(dest_path, 'wb') as fd:
            fd.write(res.content)  # res.text is str, res.content is bytes
        return {
            'feedpath': dest_path,
            'rss_link': link,
            'failed': False,
            'error': None
        }

    def handle_304(): return {
        'feedpath': dest_path,
        'rss_link': link,
        'failed': False,
        'error': None
    }

    def handle_301_302():
        n_link = res.headers.get('location', link)
        confman.conf['feeds'][n_link] = confman.conf['feeds'][link]
        confman.conf['feeds'].pop(link)
        return download_feed(n_link)

    def handle_everything_else(): return {
        'feedpath': None,
        'rss_link': link,
        'failed': True,
        'error': _('Error downloading `{0}`, code `{1}`').format(
            link, res.status_code
        )
    }

    handlers = {
        200: handle_200, 304: handle_304,
        301: handle_301_302, 302: handle_301_302
    }
    return handlers.get(res.status_code, handle_everything_else)()
