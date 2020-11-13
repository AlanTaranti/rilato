from gettext import gettext as _
from urllib.parse import urlparse
from lxml.html import html5parser
from PIL import Image
from gfeeds.download_manager import download_raw, download_text


def get_favicon(link, favicon_path):
    # req = requests.get(link)
    # if not 200 <= req.status_code <= 299:
    #     print(f'get_favicon: failed with code {req.status_code}')
    #     return None
    html = download_text(link)
    root = html5parser.fromstring(
        html if isinstance(html, str) else html.decode()
    )
    favicon_els = root.xpath(
        '//x:link',
        namespaces={'x': 'http://www.w3.org/1999/xhtml'}
    )
    candidate = {
        'path': '',
        'is_absolute': False,
        'size': -1
    }
    for e in favicon_els:
        if candidate['size'] >= 100:
            break
        if 'rel' in e.attrib.keys():
            size = 0
            can_save = False
            if e.attrib['rel'] == 'apple-touch-icon':
                size = 1
                can_save = True
                if 'sizes' in e.attrib.keys():
                    size = int(e.attrib['sizes'].split('x')[0])
            elif (
                    e.attrib['rel'] in ['icon', 'shortcut icon'] and
                    candidate['size'] == -1
            ):
                size = 0
                can_save = True
            if can_save:
                candidate['path'] = e.attrib['href']
                candidate['is_absolute'] = (
                    'http://' in e.attrib['href'] or
                    'https://' in e.attrib['href']
                )
                candidate['size'] = size
    p = candidate['path']
    needs_convert = False
    if not p:
        return
    if p[-4:].lower() == '.ico':
        needs_convert = True
    if not candidate['is_absolute']:
        if p[0:2] == '//':
            p = p[2:]
        elif p[0] == '/':
            p = p[1:]
        up = urlparse(link)
        url = f'{up.scheme or "http"}://{up.hostname}/{p}'
        try:
            download_raw(url, favicon_path)
        except Exception:
            try:
                url = f'{up.scheme or "http"}://{p}'
                download_raw(url, favicon_path)
            except Exception:
                print(_('Error downloading favicon for `{0}`').format(link))
    else:
        download_raw(p, favicon_path)
    if needs_convert:
        toconv = Image.open(favicon_path)
        toconv.save(favicon_path)
        toconv.close()
