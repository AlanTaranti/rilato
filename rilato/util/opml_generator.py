from typing import Iterable, TYPE_CHECKING
from xml.sax.saxutils import quoteattr

if TYPE_CHECKING:
    from rilato.feed import Feed


OPML_PREFIX = '''<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head>
    <title>Subscriptions</title>
  </head>
  <body>
'''

OPML_SUFFIX = '''  </body>
</opml>'''


def __outline(
        title: str, text: str, xml_url: str, html_url: str, category: str
) -> str:
    return (
        '<outline type="rss" '
        f'title={quoteattr(title)} '
        f'text={quoteattr(text)} '
        f'xmlUrl={quoteattr(xml_url)} '
        f'htmlUrl={quoteattr(html_url)} '
        f'category={quoteattr(category)} '
        '/>'
    )


def feeds_list_to_opml(feeds: Iterable['Feed']):
    opml_out = OPML_PREFIX
    for f in feeds:
        categories = (f.get_conf_dict() or dict()).get('tags', [])
        categories = ','.join(categories)
        opml_out += '    ' + __outline(
            f.title, f.description, f.rss_link, f.link,  # type: ignore
            categories
        ) + '\n'
    opml_out += OPML_SUFFIX
    return opml_out
