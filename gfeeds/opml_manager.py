from gi.repository import GLib
from gettext import gettext as _
from threading import Thread
from os.path import isfile
from xml.sax.saxutils import quoteattr
from gfeeds.confManager import ConfManager
from gfeeds.feeds_manager import FeedsManager
from syndom import Opml

confman = ConfManager()
feedman = FeedsManager()


def __add_feeds_from_opml_callback():
    feedman.refresh()


def __add_feeds_from_opml_worker(opml_path):
    n_feeds_urls_l = opml_to_rss_list(opml_path)
    for tag in [t for f in n_feeds_urls_l for t in f['tags']]:
        feedman.tag_store.add_tag(tag)
    for f in n_feeds_urls_l:
        url = f['feed']
        if url not in confman.conf['feeds'].keys():
            confman.conf['feeds'][url] = {
                'tags': f['tags']
            }
    confman.save_conf()
    GLib.idle_add(__add_feeds_from_opml_callback)


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
        sd_opml = Opml(opml_path, True)
        res = [
            {'feed': item.get_feed_url(), 'tags': item.get_categories()}
            for item in sd_opml.get_items()
        ]
    except Exception:
        import traceback
        traceback.print_exc()
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
        categories = confman.conf['feeds'][f.rss_link].get('tags', list())
        categories = ','.join(categories)
        opml_out += f'''
            <outline
                title={quoteattr(f.title)}
                text={quoteattr(f.description)}
                type="rss"
                xmlUrl={quoteattr(f.rss_link)}
                htmlUrl={quoteattr(f.link)}
                category={quoteattr(categories)}
            />
        '''
    opml_out += OPML_SUFFIX
    return opml_out
