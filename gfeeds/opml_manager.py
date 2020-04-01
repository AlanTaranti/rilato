from gi.repository import GLib
from gettext import gettext as _
import listparser
from threading import Thread
from os.path import isfile
from xml.sax.saxutils import escape
from gfeeds.confManager import ConfManager
from gfeeds.feeds_manager import FeedsManager

confman = ConfManager()
feedman = FeedsManager()


def __add_feeds_from_opml_callback(n_feeds_urls_l):
    for url in n_feeds_urls_l:
        if url not in confman.conf['feeds'].keys():
            confman.conf['feeds'][url] = {}
    feedman.refresh()


def __add_feeds_from_opml_worker(opml_path):
    n_feeds_urls_l = opml_to_rss_list(opml_path)
    GLib.idle_add(
        __add_feeds_from_opml_callback,
        n_feeds_urls_l
    )


def add_feeds_from_opml(opml_path):
    t = Thread(target=__add_feeds_from_opml_worker, args=(opml_path,))
    t.start()


def opml_to_rss_list(opml_path):
    if not isfile(opml_path):
        print(_('Error: OPML path provided does not exist'))
        return []
    try:
        lp_opml = listparser.parse(opml_path)
        n_feeds_urls_l = [f['url'] for f in lp_opml['feeds']]
        return n_feeds_urls_l
    except Exception:
        print(_('Error parsing OPML file `{0}`').format(opml_path))
        return []


OPML_PREFIX = '''<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head>
    <title>Subscriptions</title>
  </head>
  <body>
'''

OPML_SUFFIX = '''
  </body>
</opml>
'''


def feeds_list_to_opml(feeds):
    opml_out = OPML_PREFIX
    for f in feeds:
        opml_out += f'''
            <outline
                title="{escape(f.title)}"
                text="{escape(f.description)}"
                type="rss"
                xmlUrl="{escape(f.rss_link)}"
                htmlUrl="{escape(f.link)}"
            />
        '''
    opml_out += OPML_SUFFIX
    return opml_out
