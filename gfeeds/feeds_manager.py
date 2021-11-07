import threading
from gettext import gettext as _
from gi.repository import GLib, GObject
from gfeeds.singleton import Singleton
from gfeeds.confManager import ConfManager
from gfeeds.rss_parser import Feed
from gfeeds.download_manager import (
    download_feed,
    extract_feed_url_from_html
)
from gfeeds.signaler_list import SignalerList
from gfeeds.test_connection import is_online
from gfeeds.thread_pool import ThreadPool


class FeedsManagerSignaler(GObject.Object):
    __gsignals__ = {
        'feedmanager_refresh_start': (
            GObject.SignalFlags.RUN_LAST,
            None,
            (str,)
        ),
        'feedmanager_refresh_end': (
            GObject.SignalFlags.RUN_LAST,
            None,
            (str,)
        ),
        'feedmanager_online_changed': (
            GObject.SignalFlags.RUN_LAST,
            None,
            (bool,)
        ),
    }


class FeedsManager(metaclass=Singleton):
    def __init__(self):
        self.confman = ConfManager()
        self.confman.connect(
            'gfeeds_repopulation_required',
            self.refresh
        )
        self.signaler = FeedsManagerSignaler()
        self.emit = self.signaler.emit
        self.connect = self.signaler.connect

        self.feeds = SignalerList()
        self.feeds_items = SignalerList()

        self.errors = []
        self.problematic_feeds = []
        self.connect(
            'feedmanager_refresh_end',
            lambda *args: self.confman.save_conf()
        )

    def _add_feed_async_worker(
            self,
            uri: str,
            refresh: bool = False,
            get_cached: bool = False
    ):
        if not refresh:
            if 'http://' not in uri and 'https://' not in uri:
                uri = 'http://' + uri
            if uri in self.confman.conf['feeds'].keys():
                print(_('Feed {0} exists already, skipping').format(uri))
                return
            self.confman.conf['feeds'][uri] = {}
        download_res = download_feed(uri, get_cached=get_cached)
        if get_cached and download_res[0] == 'not_cached':
            return
        n_feed = Feed(download_res)
        if n_feed.is_null:
            feed_uri_from_html = extract_feed_url_from_html(uri)
            if feed_uri_from_html is not None:
                if uri in self.confman.conf['feeds'].keys():
                    self.confman.conf['feeds'].pop(uri)
                self._add_feed_async_worker(feed_uri_from_html, refresh)
                return
            self.errors.append(n_feed.error)
            self.problematic_feeds.append(uri)
        else:
            GLib.idle_add(
                self.feeds.append, n_feed, priority=GLib.PRIORITY_LOW
            )
            GLib.idle_add(
                self.feeds_items.extend,
                n_feed.items,
                priority=GLib.PRIORITY_LOW
            )
        if not refresh:
            GLib.idle_add(
                self.emit, 'feedmanager_refresh_end', ''
            )

    def refresh(
            self,
            *args,
            get_cached: bool = False,
            is_startup: bool = False
    ):
        self.emit(
            'feedmanager_refresh_start',
            'startup' if is_startup else ''
        )
        self.errors = []
        self.problematic_feeds = []

        def cb(res):
            _get_cached = get_cached
            if res:
                self.emit('feedmanager_online_changed', True)
            else:
                self.emit('feedmanager_online_changed', False)
                _get_cached = True
                # self.emit('feedmanager_refresh_end', '')
                # return
            self.continue_refresh(_get_cached)

        is_online(cb)

    def continue_refresh(self, get_cached):
        self.feeds.empty()
        self.feeds_items.empty()
        tp = ThreadPool(
            self.confman.conf['max_refresh_threads'],
            self._add_feed_async_worker,
            [
                (f_link, True, get_cached)
                for f_link in self.confman.conf['feeds'].keys()
            ],
            self.emit,
            ('feedmanager_refresh_end', '')
        )
        tp.start()

    def add_feed(self, uri: str, is_new: bool = False) -> bool:
        if is_new and uri in self.confman.conf['feeds'].keys():
            return False
        self.emit('feedmanager_refresh_start', '')
        self.errors = []
        t = threading.Thread(
            group=None,
            target=self._add_feed_async_worker,
            name=None,
            args=(uri,)
        )
        t.start()
        return True

    def delete_feeds(self, targets, *args):
        if type(targets) != list:
            if type(targets) == Feed:
                targets = [targets]
            else:
                raise TypeError('delete_feed: targets must be list or Feed')
        for f in targets:
            for fi in f.items:
                self.feeds_items.remove(fi)
            self.feeds.remove(f)
            self.confman.conf['feeds'].pop(
                f.rss_link
            )
        self.confman.save_conf()
