from gettext import gettext as _
from urllib.parse import urlparse
from PIL import Image
from os.path import isfile
from gfeeds.download_manager import download_raw
from gfeeds.sha import shasum
from gfeeds.confManager import ConfManager
from syndom import Html

confman = ConfManager()
VALID_ICON_FORMATS = ['.png', '.jpg', '.svg', '.gif']


def get_favicon(link, favicon_path):
    try:
        page_dest = str(
            confman.cache_path.joinpath(shasum(link)+'.html')
        )
        if not isfile(page_dest):
            download_raw(link, page_dest)
        sd_html = Html(page_dest)
        url = sd_html.icon_url
        if not url:
            return
    except Exception:
        return
    p = url
    if '?' in p:
        p = p.split('?')[0]
    needs_convert = (
        p[-4:].lower() not in VALID_ICON_FORMATS and
        not p[-5:].lower() == '.jpeg'
    )
    if not ('http://' in url or 'https://' in url):
        target = url.lstrip('/')
        up = urlparse(link)
        target = f'{up.scheme or "http"}://{up.hostname}/{target}'
        try:
            download_raw(target, favicon_path)
        except Exception:
            try:
                target = f'{up.scheme or "http"}://{url}'
                download_raw(target, favicon_path)
            except Exception:
                print(_('Error downloading favicon for `{0}`').format(link))
                return
    else:
        download_raw(url, favicon_path)
    if needs_convert:
        toconv = Image.open(favicon_path)
        toconv.save(favicon_path)
        toconv.close()
