from gi.repository import GLib, Adw
from gfeeds.confManager import ConfManager
from gfeeds.feeds_manager import FeedsManager
from gfeeds.articles_listview import ArticlesListView, ArticlesListBox


class GFeedsSidebar(Adw.Bin):
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

        self.set_child(self.listview_sw)

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

        self.feedman.feeds.connect(
            'pop',
            lambda caller, obj: self.on_feeds_pop(obj)
        )

    def on_feeds_items_extend(self, caller, n_feeds_items_list):
        self.listview_sw.add_new_items(n_feeds_items_list)

    def on_feeds_pop(self, obj):
        if obj.rss_link in self.listview_sw.selected_feeds:
            n_selected_feeds = self.listview_sw.selected_feeds
            n_selected_feeds.remove(obj.rss_link)
            self.listview_sw.set_selected_feeds(n_selected_feeds)
        self.listview_sw.remove_items(obj.items)

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
