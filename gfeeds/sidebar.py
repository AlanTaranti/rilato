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

    def on_refresh_start(self, *_):
        self.loading_revealer.set_running(True)

    def on_refresh_end(self, *_):
        self.listview_sw.all_items_changed()
        self.loading_revealer.set_running(False)

    def on_feed_removed(self, _, feed: Feed):
        if feed.rss_link in self.listview_sw.selected_feeds:
            n_selected_feeds = self.listview_sw.selected_feeds
            n_selected_feeds.remove(feed.rss_link)
            self.listview_sw.set_selected_feeds(n_selected_feeds)

    def set_search(self, search_term):
        self.listview_sw.set_search_term(search_term)

    def select_next_article(self, *_):
        self.listview_sw.select_next()

    def select_prev_article(self, *_):
        self.listview_sw.select_prev()
