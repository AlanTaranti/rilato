from threading import Thread, Event
from gettext import gettext as _
from typing import List, Union
from gi.repository import GLib, GObject
from gfeeds.articles_listmodel import ArticlesListModel
from gfeeds.util.singleton import Singleton
from gfeeds.confManager import ConfManager
from gfeeds.feed import Feed
from gfeeds.feed_parser import FeedParser
from gfeeds.util.download_manager import (
    download_feed,
    extract_feed_url_from_html
)
from gfeeds.tag_store import TagStore
from gfeeds.util.test_connection import is_online
from gfeeds.util.thread_pool import ThreadPool
from gfeeds.feed_store import FeedStore
import pytz
from datetime import datetime


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

        self.feed_store = FeedStore()
        self.tag_store = TagStore()
        self.article_store = ArticlesListModel()

        self.errors = []
        self.problematic_feeds = []
        self.new_items_num = 0  # for the notification, resets on refresh

        self.__auto_refresh_event = Event()
        self.auto_refresh_thread = None
        self.connect(
            'feedmanager_refresh_end',
            self.on_refresh_end
        )

    def on_refresh_end(self, *args):
        self.confman.save_conf()
        # new articles notified in app_window
        self.start_auto_refresh()

    def __increment_new_items_num(self):
        # dumb thing to have in a function, it's because it's to be called
        # from the main thread and lambdas apparently can't do it
        self.new_items_num += 1

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
        if get_cached and download_res['feedpath'] == 'not_cached':
            return
        parser = FeedParser()
        parser.parse(
            feedpath=download_res['feedpath'],
            rss_link=download_res['rss_link'],
            failed=download_res['failed'],
            error=download_res['error']
        )
        if parser.is_null:
            feed_uri_from_html = extract_feed_url_from_html(uri)
            if feed_uri_from_html is not None:
                if uri in self.confman.conf['feeds'].keys():
                    self.confman.conf['feeds'].pop(uri)
                self._add_feed_async_worker(feed_uri_from_html, refresh)
                return
            self.errors.append(parser.error)
            self.problematic_feeds.append(uri)
        else:
            n_feed = self.feed_store.get_feed(
                parser.feed_identifier
            )
            if n_feed is None:
                n_feed = Feed(self.tag_store)
                GLib.idle_add(
                    self.feed_store.add_feed, n_feed,
                    priority=GLib.PRIORITY_LOW
                )
            n_feed.populate(parser)
            for fi in n_feed.items.values():
                if (
                        n_feed.rss_link+fi.identifier not in
                        [
                            ofi.parent_feed.rss_link+ofi.identifier
                            for ofi in self.article_store.list_store
                            if ofi
                        ]
                ):
                    GLib.idle_add(
                        self.article_store.add_new_items,
                        [fi],
                        priority=GLib.PRIORITY_LOW
                    )
                    if not get_cached:
                        GLib.idle_add(self.__increment_new_items_num)
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
        self.new_items_num = 0

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
        self.trim_feeds_items_by_age()
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

    def trim_feeds_items_by_age(self):
        now = pytz.UTC.localize(datetime.utcnow())
        to_rm = []
        for item in self.article_store.list_store:
            item_age = now - item.pub_date
            if item_age > self.confman.max_article_age:
                to_rm.append(item)
        self.article_store.remove_items(to_rm)

    def start_auto_refresh(self):
        if self.auto_refresh_thread is not None:
            if self.auto_refresh_thread.is_alive():
                self.__auto_refresh_event.set()
                self.auto_refresh_thread.join()
        self.__auto_refresh_event.clear()
        if self.confman.conf['auto_refresh_enabled']:
            self.auto_refresh_thread = Thread(
                target=self._auto_refresh_worker, daemon=True
            ).start()

    def _auto_refresh_worker(self):
        if not self.confman.conf['auto_refresh_enabled']:
            self.__auto_refresh_event.clear()
            return
        # when event.wait returns True the flag has been manually set, so in
        # case, it means a manual refresh occurred, so we can terminate the
        # auto-refresh for now
        if self.__auto_refresh_event.wait(
                self.confman.conf['auto_refresh_time_seconds']
        ):
            self.__auto_refresh_event.clear()
            return
        # if False, the timeout has been reached, so we do the auto refresh
        self.__auto_refresh_event.clear()
        GLib.idle_add(self.refresh)

    def add_feed(self, uri: str, is_new: bool = False) -> bool:
        if is_new and uri in self.confman.conf['feeds'].keys():
            return False
        self.emit('feedmanager_refresh_start', '')
        self.errors = []
        t = Thread(
            target=self._add_feed_async_worker,
            args=(uri,),
            daemon=True
        )
        t.start()
        return True

    def delete_feeds(self, targets: Union[List[Feed], Feed], *_):
        if not isinstance(targets, list):
            if isinstance(targets, Feed):
                targets = [targets]
            else:
                raise TypeError('delete_feed: targets must be list or Feed')
        articles_to_rm = []
        n_selected_feeds = self.article_store.selected_feeds.copy()
        for to_rm in targets:
            articles_to_rm.extend([i[1] for i in to_rm.items.items()])
            if to_rm.rss_link in n_selected_feeds:
                n_selected_feeds.remove(to_rm.rss_link)
            self.feed_store.remove_feed(to_rm)
            self.confman.conf['feeds'].pop(
                to_rm.rss_link
            )
        self.article_store.set_selected_feeds(n_selected_feeds)
        self.article_store.remove_items(articles_to_rm)
        self.confman.save_conf()
