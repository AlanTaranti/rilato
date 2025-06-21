from typing import List
from gi.repository import Gtk, Gio
from rilato.feed_item import FeedItem
from rilato.confManager import ConfManager
from typing import Optional


class ArticlesListModel(Gtk.SortListModel):
    def __init__(self):
        self.selected_feeds = []
        self.selected_article = None
        self.__search_term = ''

        # this is a chain: list_store contains the raw data,
        # filter_store filters it and sort_store sorts it, then the listview
        # is fed the last link in the chain via the selection object
        self.filter = Gtk.CustomFilter()
        self.filter.set_filter_func(self._filter_func)
        self.sorter = Gtk.CustomSorter()
        self.sorter.set_sort_func(self._sort_func)
        self.list_store = Gio.ListStore(item_type=FeedItem)
        self.filter_store = Gtk.FilterListModel(
            model=self.list_store, filter=self.filter
        )
        self.confman = ConfManager()
        super().__init__(model=self.filter_store, sorter=self.sorter)

        self.confman.connect(
            'rilato_show_read_changed', lambda *_: self.invalidate_filter()
        )
        self.confman.connect(
            'rilato_new_first_changed', lambda *_: self.invalidate_sort()
        )
        self.confman.connect(
            'rilato_filter_changed', self._change_filter
        )

    def set_all_read_state(self, state: bool):
        for feed_item in self.list_store:
            if not feed_item:
                continue
            if self.__filter_by_feed_and_search(feed_item):
                feed_item.read = state
        if not self.confman.nconf.show_read_items and not state:
            self.invalidate_filter()

    def _change_filter(self, caller, n_filter):
        if n_filter is None:
            self.selected_feeds = []
        elif isinstance(n_filter, list):
            n_filter = n_filter[0]
            # filter by tag
            self.selected_feeds = [
                f for f in self.confman.nconf.feeds.keys()
                if 'tags' in self.confman.nconf.feeds[f].keys() and
                n_filter in self.confman.nconf.feeds[f]['tags']
            ]
        else:
            self.selected_feeds = [n_filter.rss_link]
        self.invalidate_filter()

    def set_selected_article(self, n_selected: Optional[FeedItem]):
        self.selected_article = n_selected
        self.invalidate_filter()

    def _filter_func(self, item: FeedItem, *_) -> bool:
        res = self.__filter_by_feed_and_search(item)
        if not self.confman.nconf.show_read_items:
            res = res and (
                item == self.selected_article or
                not item.read
            )
        return res

    def __filter_by_feed_and_search(self, item: FeedItem) -> bool:
        res = True
        if len(self.selected_feeds) > 0:
            res = item.parent_feed.rss_link in self.selected_feeds
        if self.__search_term:
            res = res and (
                self.__search_term in item.title.lower()
            )
        return res

    def _sort_func(self, item1: FeedItem, item2: FeedItem, *_) -> int:
        # item1 first -> -1
        # item2 first -> +1
        # equal (unused) -> 0
        if self.confman.nconf.new_first:
            return (
                -1 if item1.pub_date > item2.pub_date  # type: ignore
                else 1
            )
        return (
            -1 if item1.pub_date < item2.pub_date  # type: ignore
            else 1
        )

    def invalidate_filter(self):
        self.filter.set_filter_func(self._filter_func)

    def invalidate_sort(self):
        self.sorter.set_sort_func(self._sort_func)

    def empty(self):
        self.list_store.remove_all()

    def add_new_items(self, feeditems_l):
        # self.parent_stack.set_main_visible(True)
        for i in feeditems_l:
            self.list_store.append(i)

    def populate(self, feeditems_l):
        self.empty()  # TODO: review this API, doesn't make too much sense
        self.add_new_items(feeditems_l)

    def all_items_changed(self):
        for item in self.list_store:
            item.emit('changed', '')

    def remove_items(self, to_remove_l: List[FeedItem]):
        to_rm_ids = [i.identifier for i in to_remove_l]
        to_rm_indices = []
        for idx, item in enumerate(self.list_store):
            if len(to_rm_ids) <= 0:
                break
            if not item:
                continue
            if item.identifier in to_rm_ids:
                to_rm_ids.remove(item.identifier)
                to_rm_indices.append(idx)
        for idx in sorted(to_rm_indices, reverse=True):
            self.list_store.remove(idx)

    def set_search_term(self, term):
        self.__search_term = term.strip().lower()
        self.invalidate_filter()

    def set_selected_feeds(self, n_feeds_l: List[str]):
        self.selected_feeds = n_feeds_l
        self.invalidate_filter()
