from gettext import gettext as _
from urllib.parse import urlparse
from PIL import Image
from os.path import isfile
from os import remove
from gfeeds.download_manager import download_raw
from gfeeds.sha import shasum
from gfeeds.confManager import ConfManager
from syndom import Html

confman = ConfManager()

def get_favicon(link, favicon_path):
    favicon_path_orig = favicon_path + '.original'
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
    if not ('http://' in url or 'https://' in url):
        target = url.lstrip('/')
        up = urlparse(link)
        target = f'{up.scheme or "http"}://{up.hostname}/{target}'
        try:
            download_raw(target, favicon_path_orig)
        except Exception:
            try:
                target = f'{up.scheme or "http"}://{url}'
                download_raw(target, favicon_path_orig)
            except Exception:
                print(_('Error downloading favicon for `{0}`').format(link))
                return
    else:
        download_raw(url, favicon_path_orig)
    toconv = Image.open(favicon_path_orig)
    toconv.convert(mode='RGBA')
    toconv.save(favicon_path)
    toconv.close()
    remove(favicon_path_orig)
