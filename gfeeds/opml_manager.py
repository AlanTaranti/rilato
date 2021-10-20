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


def __add_feeds_from_opml_callback():
    feedman.refresh()


def __add_feeds_from_opml_worker(opml_path):
    n_feeds_urls_l = opml_to_rss_list(opml_path)
    for tag in [t for f in n_feeds_urls_l for t in f['tags']]:
        confman.add_tag(tag)
    for f in n_feeds_urls_l:
        url = f['feed']
        print(url)
        if url not in confman.conf['feeds'].keys():
            confman.conf['feeds'][url] = {
                'tags': f['tags']
            }
    confman.save_conf()
    GLib.idle_add(
        __add_feeds_from_opml_callback
    )


def add_feeds_from_opml(opml_path):
    t = Thread(
        target=__add_feeds_from_opml_worker, args=(opml_path,), daemon=True
    )
    t.start()


def opml_to_rss_list(opml_path):
    res = []
    if not isfile(opml_path):
        print(_('Error: OPML path provided does not exist'))
        return res
    try:
        with open(opml_path, 'r') as fd:
            lp_opml = listparser.parse(fd.read())
            res = [
                {'feed': f['url'], 'tags': f['tags']} for f in lp_opml['feeds']
            ]
    except Exception:
        print(_('Error parsing OPML file `{0}`').format(opml_path))
    return res


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
                category="{escape(
                    ','.join(confman.conf['feeds'][f.rss_link]['tags'])
                ) if 'tags' in confman.conf['feeds'][f.rss_link].keys()
                else ''}"
            />
        '''
    opml_out += OPML_SUFFIX
    return opml_out
