from gettext import gettext as _
from os.path import isfile
import requests
from lxml.html import html5parser
from gfeeds.confManager import ConfManager
from gfeeds.sha import shasum
from gfeeds.url_sanitizer import sanitize

confman = ConfManager()

GET_HEADERS = {
    'User-Agent': 'gfeeds/1.0',
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate'
}

TIMEOUT = 30


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
        print(f'response code {res.status_code}')
        raise requests.HTTPError(f'response code {res.status_code}')


def download_raw(link: str, dest: str):
    res = requests.get(link, headers=GET_HEADERS, timeout=TIMEOUT)
    if res.status_code == 200:
        with open(dest, 'wb') as fd:
            for chunk in res.iter_content(1024):
                fd.write(chunk)
    else:
        raise requests.HTTPError(
            f'response code {res.status_code} for url `{link}`'
        )


def extract_feed_url_from_html(link: str) -> str:
    try:
        html = download_text(link)
        root = html5parser.fromstring(
            html if type(html) == str else html.decode()
        )
        link_els = root.xpath(
            '//x:link',
            namespaces={'x': 'http://www.w3.org/1999/xhtml'}
        )
        for el in link_els:
            if (
                el.attrib.get('rel', '') == 'alternate' and
                el.attrib.get('type', '') in (
                    'application/atom+xml', 'application/rss+xml'
                ) and 'href' in el.attrib.keys()
            ):
                return sanitize(link, el.attrib['href'])
    except Exception:
        print('exception in `extract_feed_from_html`')
    return None


# TODO: refactor this, the returned typeS(!) are a mess
def download_feed(link: str, get_cached: bool = False):
    dest_path = confman.cache_path.joinpath(shasum(link)+'.rss')
    if get_cached:
        return (dest_path, link) if isfile(dest_path) else ('not_cached', None)
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
        return (False, _('`{0}`: connection timed out').format(link))
    except Exception:
        import traceback
        traceback.print_exc()
        return (False, _('`{0}` might not be a valid address').format(link))
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
        return (dest_path, link)

    def handle_304(): return (dest_path, link)

    def handle_301_302():
        n_link = res.headers.get('location', link)
        confman.conf['feeds'][n_link] = confman.conf['feeds'][link]
        confman.conf['feeds'].pop(link)
        return download_feed(n_link)

    def handle_everything_else(): return (
        False,
        _('Error downloading `{0}`, code `{1}`').format(link, res.status_code)
    )

    handlers = {
        200: handle_200, 304: handle_304,
        301: handle_301_302, 302: handle_301_302
    }
    return handlers.get(res.status_code, handle_everything_else)()
