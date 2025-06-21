from gettext import gettext as _
from os.path import isfile
from pathlib import Path
import requests
from rilato.confManager import ConfManager
from rilato.util.create_full_url import create_full_url
from rilato.util.paths import CACHE_PATH
from rilato.util.sha import shasum
from rilato.util.html_parser import Html
from typing import Literal, Optional, Union
from rilato.util.to_unicode import to_unicode, bytes_to_unicode

GET_HEADERS = {
    "User-Agent": "rilato/1.0",
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate",
}

TIMEOUT = 30


class DownloadError(Exception):
    def __init__(self, code, *args):
        self.download_error_code = code


# will return the content of a file if it's a file url
def download_text(link: str) -> str:
    if link[:8] == "file:///":
        with open(link[7:]) as fd:
            toret = fd.read()
        return toret
    res = requests.get(link, headers=GET_HEADERS, timeout=TIMEOUT)
    if 200 <= res.status_code <= 299:
        return bytes_to_unicode(res.content, enc=res.encoding)
    else:
        raise DownloadError(res.status_code, f"response code {res.status_code}")


def download_raw(link: str, dest: str) -> None:
    res = requests.get(link, headers=GET_HEADERS, timeout=TIMEOUT)
    if res.status_code == 200:
        with open(dest, "wb") as fd:
            for chunk in res.iter_content(1024):
                fd.write(chunk)
    else:
        raise requests.HTTPError(f"response code {res.status_code} for url `{link}`")


def extract_feed_url_from_html(link: str) -> Optional[str]:
    dest = str(CACHE_PATH.joinpath(shasum(link) + ".html"))
    try:
        if not isfile(dest):
            download_raw(link, dest)
        sd_html = Html(dest)
        res: str = sd_html.rss_url
        if not res:
            return None
        res = create_full_url(link, res)
        return res
    except Exception:
        print("Error extracting feed from HTML")
    return None


class DownloadFeedResponse:
    def __init__(
        self,
        feedpath: Optional[Union[Path, Literal["not_cached"]]],
        rss_link: Optional[str],
        failed: bool,
        error: Optional[str],
    ):
        self.feedpath = feedpath
        self.rss_link = rss_link
        self.failed = failed
        self.error = error


def download_feed(link: str, get_cached: bool = False) -> DownloadFeedResponse:
    confman = ConfManager()

    dest_path: Path = CACHE_PATH.joinpath(shasum(link) + ".rss")
    if get_cached:
        return DownloadFeedResponse(
            dest_path if isfile(dest_path) else "not_cached",
            link,
            not isfile(dest_path),
            None,
        )
    headers = GET_HEADERS.copy()
    if "last-modified" in confman.nconf.feeds[link].keys() and isfile(dest_path):
        headers["If-Modified-Since"] = confman.nconf.feeds[link]["last-modified"]
    try:
        res = requests.get(link, headers=headers, allow_redirects=True, timeout=TIMEOUT)
    except requests.exceptions.ConnectTimeout:
        return DownloadFeedResponse(
            None, link, True, _("`{0}`: connection timed out").format(link)
        )
    except Exception:
        import traceback

        traceback.print_exc()
        return DownloadFeedResponse(
            None, link, True, _("`{0}` might not be a valid address").format(link)
        )
    if "last-modified" in res.headers.keys():
        # TODO fix when switching to non-json feeds in gsettings
        feeds: dict = confman.nconf.feeds
        feeds[link]["last-modified"] = res.headers["last-modified"]
        confman.nconf.feeds = feeds

    def handle_200():
        if (
            "last-modified" not in res.headers.keys()
            and "last-modified" in confman.nconf.feeds[link].keys()
        ):
            feeds: dict = confman.nconf.feeds
            feeds[link].pop("last-modified")
            confman.nconf.feeds = feeds
        with open(dest_path, "wb") as fd:
            fd.write(res.content)  # res.text is str, res.content is bytes
        to_unicode(dest_path)
        return DownloadFeedResponse(dest_path, link, False, None)

    def handle_304():
        return DownloadFeedResponse(dest_path, link, False, None)

    def handle_301_302():
        n_link = res.headers.get("location", link)
        feeds: dict = confman.nconf.feeds
        feeds[n_link] = feeds[link]
        feeds.pop(link)
        confman.nconf.feeds = feeds
        return download_feed(n_link)

    def handle_everything_else():
        return DownloadFeedResponse(
            None,
            link,
            True,
            _("Error downloading `{0}`, code `{1}`").format(link, res.status_code),
        )

    handlers = {
        200: handle_200,
        304: handle_304,
        301: handle_301_302,
        302: handle_301_302,
    }
    return handlers.get(res.status_code, handle_everything_else)()
