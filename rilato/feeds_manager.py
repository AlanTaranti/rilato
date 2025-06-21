from pathlib import Path
from threading import Thread, Event
from gettext import gettext as _
from typing import Iterable, List, Union, cast
from gi.repository import GLib, GObject
from rilato.articles_listmodel import ArticlesListModel
from rilato.util.opml_parser import opml_to_rss_list
from rilato.util.singleton import Singleton
from rilato.confManager import ConfManager
from rilato.feed import Feed
from rilato.feed_parser import parse_feed
from rilato.util.download_manager import download_feed, extract_feed_url_from_html
from rilato.tag_store import TagStore
from rilato.util.test_connection import is_online
from rilato.util.thread_pool import ThreadPool
from rilato.feed_store import FeedStore
from rilato.signal_helper import signal_tuple
import pytz
from datetime import datetime


class FeedsManagerSignaler(GObject.Object):
    __gsignals__ = {
        "feedmanager_refresh_start": signal_tuple(params=(str,)),
        "feedmanager_refresh_end": signal_tuple(params=(str,)),
        "feedmanager_online_changed": signal_tuple(params=(bool,)),
        "feedmanager_feeds_loaded_changed": signal_tuple(params=(float,)),
    }


class FeedsManager(metaclass=Singleton):
    def __init__(self):
        self.confman = ConfManager()
        self.confman.connect("rilato_repopulation_required", self.refresh)
        self.signaler = FeedsManagerSignaler()
        self.emit = self.signaler.emit
        self.connect = self.signaler.connect

        self.feed_store = FeedStore()
        self.tag_store = TagStore()
        self.article_store = ArticlesListModel()

        self.errors = []
        self.problematic_feeds = []
        self.new_items_num = 0  # for the notification, resets on refresh

        self.is_refreshing = False
        self.__auto_refresh_event = Event()
        self.auto_refresh_thread = None
        self.connect("feedmanager_refresh_end", self.on_refresh_end)

        self.__feeds_loaded = 0

    def on_refresh_end(self, *__):
        # new articles notified in app_window
        self.start_auto_refresh()

    def __increment_new_items_num(self):
        # dumb thing to have in a function, it's because it's to be called
        # from the main thread and lambdas apparently can't do it
        self.new_items_num += 1

    def _add_feed_async_worker(
        self, uri: str, refresh: bool = False, get_cached: bool = False
    ):
        self.__tick_feeds_loaded()
        if not refresh:
            if not (uri.startswith("http://") or uri.startswith("https://")):
                uri = "http://" + uri
            if uri in self.confman.nconf.feeds.keys():
                print(_("Feed {0} exists already, skipping").format(uri))
                GLib.idle_add(self.emit, "feedmanager_refresh_end", "")
                return
            feeds = self.confman.nconf.feeds
            feeds[uri] = {}
            self.confman.nconf.feeds = feeds
        download_res = download_feed(uri, get_cached=get_cached)
        if get_cached and download_res.feedpath == "not_cached":
            return
        assert not isinstance(download_res.feedpath, str)
        parser_res = parse_feed(
            feedpath=download_res.feedpath,
            rss_link_=download_res.rss_link,
            failed=download_res.failed,
            error=download_res.error,
        )
        if parser_res.is_null:
            feed_uri_from_html = extract_feed_url_from_html(uri)
            if feed_uri_from_html is not None:
                feeds = self.confman.nconf.feeds
                if uri in feeds.keys():
                    feeds.pop(uri)
                self.confman.nconf.feeds = feeds
                self._add_feed_async_worker(feed_uri_from_html, refresh)
                return
            self.errors.append(parser_res.error)
            self.problematic_feeds.append(uri)
        else:
            n_feed = self.feed_store.get_feed(parser_res.feed_identifier)
            if n_feed is None:
                n_feed = Feed(
                    rss_link=parser_res.rss_link,
                    title=parser_res.title,
                    link=parser_res.link,
                    description=parser_res.description,
                    image_url=parser_res.image_url,
                    favicon_path=parser_res.favicon_path,
                    sd_feed=parser_res.sd_feed,
                    raw_entries=parser_res.raw_entries,
                )
                GLib.idle_add(
                    self.feed_store.add_feed, n_feed, priority=GLib.PRIORITY_LOW
                )
            else:
                n_feed.update(
                    rss_link=parser_res.rss_link,
                    title=parser_res.title,
                    link=parser_res.link,
                    description=parser_res.description,
                    image_url=parser_res.image_url,
                    favicon_path=parser_res.favicon_path,
                    sd_feed=parser_res.sd_feed,
                    raw_entries=parser_res.raw_entries,
                )
            for fi in n_feed.items.values():
                if n_feed.rss_link + fi.identifier not in [
                    ofi.parent_feed.rss_link + ofi.identifier
                    for ofi in self.article_store.list_store
                    if ofi
                ]:
                    GLib.idle_add(
                        self.article_store.add_new_items,
                        [fi],
                        priority=GLib.PRIORITY_LOW,
                    )
                    if not get_cached:
                        GLib.idle_add(self.__increment_new_items_num)
        if not refresh:
            GLib.idle_add(self.emit, "feedmanager_refresh_end", "")

    def refresh(self, *__, get_cached: bool = False, is_startup: bool = False):
        self.__feeds_loaded = 0
        self.is_refreshing = True
        self.emit("feedmanager_refresh_start", "startup" if is_startup else "")
        self.errors = []
        self.problematic_feeds = []
        self.new_items_num = 0

        def cb(res):
            _get_cached = get_cached
            if res:
                self.emit("feedmanager_online_changed", True)
            else:
                self.emit("feedmanager_online_changed", False)
                _get_cached = True
                # self.emit('feedmanager_refresh_end', '')
                # return
            self.continue_refresh(_get_cached)

        is_online(cb)

    def __signal_refresh_end(self):
        self.emit("feedmanager_refresh_end", "")
        self.is_refreshing = False

    def continue_refresh(self, get_cached):
        self.trim_feeds_items_by_age()
        tp = ThreadPool(
            self.confman.nconf.max_refresh_threads,
            self._add_feed_async_worker,
            [(f_link, True, get_cached) for f_link in self.confman.nconf.feeds.keys()],
            self.__signal_refresh_end,
            tuple(),
        )
        tp.start()

    def trim_feeds_items_by_age(self):
        now = pytz.UTC.localize(datetime.utcnow())
        to_rm = []
        for item in cast(Iterable, self.article_store.list_store):
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
        if self.confman.nconf.auto_refresh_enabled:
            self.auto_refresh_thread = Thread(
                target=self._auto_refresh_worker, daemon=True
            ).start()

    def _auto_refresh_worker(self):
        if not self.confman.nconf.auto_refresh_enabled:
            self.__auto_refresh_event.clear()
            return
        # when event.wait returns True the flag has been manually set, so in
        # case, it means a manual refresh occurred, so we can terminate the
        # auto-refresh for now
        if self.__auto_refresh_event.wait(self.confman.nconf.auto_refresh_time_seconds):
            self.__auto_refresh_event.clear()
            return
        # if False, the timeout has been reached, so we do the auto refresh
        self.__auto_refresh_event.clear()
        GLib.idle_add(self.refresh)

    def add_feed(self, uri: str, is_new: bool = False) -> bool:
        if is_new and uri in self.confman.nconf.feeds.keys():
            return False
        self.emit("feedmanager_refresh_start", "")
        self.errors = []
        t = Thread(target=self._add_feed_async_worker, args=(uri,), daemon=True)
        t.start()
        return True

    def delete_feeds(self, targets: Union[List[Feed], Feed], *_):
        if not isinstance(targets, list):
            if isinstance(targets, Feed):
                targets = [targets]
            else:
                raise TypeError("delete_feed: targets must be list or Feed")
        articles_to_rm = []
        n_selected_feeds = self.article_store.selected_feeds.copy()
        feeds = self.confman.nconf.feeds
        for to_rm in targets:
            articles_to_rm.extend(to_rm.items.values())
            if to_rm.rss_link in n_selected_feeds:
                n_selected_feeds.remove(to_rm.rss_link)
            self.feed_store.remove_feed(to_rm)
            feeds.pop(to_rm.rss_link)
        self.confman.nconf.feeds = feeds
        self.article_store.set_selected_feeds(n_selected_feeds)
        self.article_store.remove_items(articles_to_rm)

    def import_opml(self, opml_path: Union[str, Path]):
        def af(p: Union[str, Path]):
            n_feeds_urls_l = opml_to_rss_list(p)
            for tag in [t for f in n_feeds_urls_l for t in f.tags]:
                GLib.idle_add(self.tag_store.add_tag, tag)
            feeds = self.confman.nconf.feeds
            for f in n_feeds_urls_l:
                url = f.feed
                if url not in feeds.keys():
                    feeds[url] = {"tags": f.tags}
            self.confman.nconf.feeds = feeds
            GLib.idle_add(self.refresh)

        Thread(target=af, args=(opml_path,), daemon=True).start()

    def __tick_feeds_loaded(self):
        self.__feeds_loaded += 1
        self.emit(
            "feedmanager_feeds_loaded_changed",
            self.__feeds_loaded / max(len(self.confman.nconf.feeds), 1),
        )

    def cleanup_read_items(self):
        if self.is_refreshing:
            return
        avail_feed_ids = [
            fi.identifier for fi in cast(Iterable, self.article_store.list_store)
        ]
        clean_read_items = [
            item for item in self.confman.nconf.read_items if item in avail_feed_ids
        ]
        self.confman.nconf.read_items = clean_read_items
