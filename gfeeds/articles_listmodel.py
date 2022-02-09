from gi.repository import GObject, Gtk, Gio
from gfeeds.rss_parser import FeedItem
from gfeeds.confManager import ConfManager


class ArticlesListModel(Gtk.SortListModel):
    def __init__(self):
        self.selected_feeds = []
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
            'gfeeds_show_read_changed', lambda *args: self.invalidate_filter()
        )
        self.confman.connect(
            'gfeeds_new_first_changed', lambda *args: self.invalidate_sort()
        )
        self.confman.connect(
            'gfeeds_filter_changed', self._change_filter
        )

    def set_all_read_state(self, state: bool):
        for i in range(self.get_n_items()):
            feed_item = self.get_item(i)
            feed_item.read = state

    def _change_filter(self, caller, n_filter):
        if n_filter is None:
            self.selected_feeds = []
        elif isinstance(n_filter, list):
            n_filter = n_filter[0]
            # filter by tag
            self.selected_feeds = [
                f for f in self.confman.conf['feeds'].keys()
                if 'tags' in self.confman.conf['feeds'][f].keys() and
                n_filter in self.confman.conf['feeds'][f]['tags']
            ]
        else:
            self.selected_feeds = [n_filter.rss_link]
        self.invalidate_filter()

    def _filter_func(self, item: FeedItem, *args) -> bool:
        res = True
        if len(self.selected_feeds) > 0:
            res = item.parent_feed.rss_link in self.selected_feeds
        if not self.confman.conf['show_read_items']:
            res = res and (not item.read)
        if self.__search_term:
            res = res and (
                self.__search_term in item.title.lower()
            )
        return res

    def _sort_func(
            self, item1: FeedItem, item2: FeedItem, *args
    ) -> int:
        # item1 first -> -1
        # item2 first -> +1
        # equal (unused) -> 0
        if self.confman.conf['new_first']:
            return (
                -1 if item1.pub_date > item2.pub_date
                else 1
            )
        return (
            -1 if item1.pub_date < item2.pub_date
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
        for i in range(self.list_store.get_n_items()):
            self.list_store.get_item(i).emit('changed', '')

    def remove_items(self, to_remove_l):
        target_links = [fi.identifier for fi in to_remove_l]
        for item in to_remove_l:
            for index in range(len(self.list_store)):
                if item == self.list_store[index]:
                    self.list_store.remove(index)
                    break

    def set_search_term(self, term):
        self.__search_term = term.strip().lower()
        self.invalidate_filter()

    def set_selected_feeds(self, n_feeds_l):
        self.selected_feeds = n_feeds_l
        self.invalidate_filter()

    def _bind_api(self, target):
        target.empty = self.empty
        target.populate = self.populate
        target.selected_feeds = self.selected_feeds
        target.invalidate_filter = self.invalidate_filter
        target.invalidate_sort = self.invalidate_sort
        target.set_search_term = self.set_search_term
        target.set_selected_feeds = self.set_selected_feeds
        target.selected_feeds = self.selected_feeds
        target.add_new_items = self.add_new_items
        target.remove_items = self.remove_items
        target.set_all_read_state = self.set_all_read_state
        target.all_items_changed = self.all_items_changed
