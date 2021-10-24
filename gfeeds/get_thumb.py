from urllib.parse import urlparse
from html5lib import parse
from gfeeds.download_manager import download_text


def get_thumb(link):
    try:
        html = download_text(link)
        root = parse(
            html if isinstance(html, str) else html.decode(),
            namespaceHTMLElements=False
        )
    except Exception:
        return None
    meta_els = root.findall('.//head/meta')
    res = None
    for e in meta_els:
        if 'property' in e.attrib.keys() and 'content' in e.attrib.keys():
            if e.attrib['property'] in ('og:image', 'image'):
                res = e.attrib['content']
                break
    if res is None:
        return None
    if 'http://' in res or 'https://' in res:
        return res
    if res[0] == '/':
        up = urlparse(link)
        res = res.lstrip('/')
        url = f'{up.scheme or "http"}://{up.hostname}/{res}'
        return url
    return f'{link}/{res}'
