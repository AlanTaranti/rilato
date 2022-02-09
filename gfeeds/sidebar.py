from gettext import gettext as _
from gi.repository import GLib, Gtk
from gfeeds.confManager import ConfManager
from gfeeds.feeds_manager import FeedsManager
from gfeeds.articles_listview import ArticlesListView, ArticlesListBox
from gfeeds.feed_store import FeedStore
from gfeeds.rss_parser import Feed


class LoadingRevealer(Gtk.Revealer):
    def __init__(self):
        super().__init__(
            transition_type=Gtk.RevealerTransitionType.SLIDE_DOWN,
            reveal_child=False, vexpand=False, hexpand=True,
            valign=Gtk.Align.START, halign=Gtk.Align.CENTER
        )
        self.main_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=12,
            vexpand=False, hexpand=True
        )
        self.main_box.get_style_context().add_class('app-notification')
        self.label = Gtk.Label(
            label=_('Loading feeds...'), hexpand=True, vexpand=False,
            halign=Gtk.Align.CENTER
        )
        self.spinner = Gtk.Spinner(spinning=True)
        self.main_box.append(self.label)
        self.main_box.append(self.spinner)
        self.set_child(self.main_box)

    def set_running(self, state):
        self.set_reveal_child(state)


class GFeedsSidebar(Gtk.Overlay):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.confman = ConfManager()
        self.feedman = FeedsManager()

        self.listview_sw = (
            ArticlesListView()
            if self.confman.conf['use_experimental_listview']
            else ArticlesListBox()
        )
        self.empty = self.listview_sw.empty
        self.populate = self.listview_sw.populate
        self.loading_revealer = LoadingRevealer()

        self.set_child(self.listview_sw)
        self.add_overlay(self.loading_revealer)

        self.feedman.feeds_items.connect(
            'pop',
            lambda caller, obj: self.on_feeds_items_pop(obj)
        )
        self.feedman.feeds_items.connect(
            'append',
            lambda caller, obj: GLib.idle_add(
                self.on_feeds_items_append,
                obj,
                priority=GLib.PRIORITY_LOW)
        )
        self.feedman.feeds_items.connect(
            'extend',
            lambda caller, obj: GLib.idle_add(
                self.on_feeds_items_extend,
                caller,
                obj,
                priority=GLib.PRIORITY_LOW
            )
        )
        self.feedman.feeds_items.connect(
            'empty',
            lambda *args: self.listview_sw.empty()
        )

        self.feedman.feed_store.connect(
            'item-removed', self.on_feed_removed
        )
        self.feedman.connect(
            'feedmanager_refresh_start',
            self.on_refresh_start
        )
        self.feedman.connect(
            'feedmanager_refresh_end',
            self.on_refresh_end
        )

    def on_refresh_start(self, *args):
        self.loading_revealer.set_running(True)

    def on_refresh_end(self, *args):
        self.listview_sw.all_items_changed()
        self.loading_revealer.set_running(False)

    def on_feeds_items_extend(self, caller, n_feeds_items_list):
        self.listview_sw.add_new_items(n_feeds_items_list)

    def on_feed_removed(self, feed: Feed):
        if feed.rss_link in self.listview_sw.selected_feeds:
            n_selected_feeds = self.listview_sw.selected_feeds
            n_selected_feeds.remove(feed.rss_link)
            self.listview_sw.set_selected_feeds(n_selected_feeds)
        self.listview_sw.remove_items(feed.items)

    def set_search(self, search_term):
        self.listview_sw.set_search_term(search_term)

    def select_next_article(self, *args):
        self.listview_sw.select_next()

    def select_prev_article(self, *args):
        self.listview_sw.select_prev()

    def on_feeds_items_pop(self, feed_item):
        self.listview_sw.remove_items([feed_item])

    def on_feeds_items_append(self, feed_item):
        self.listview_sw.add_new_items([feed_item])
