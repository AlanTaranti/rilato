from gi.repository import GObject, Gtk, Gio
from typing import Optional
from gfeeds.confManager import ConfManager
from gfeeds.feed import Feed


class FeedStore(Gtk.FilterListModel):
    __gsignals__ = {
        'item-removed': (
            GObject.SignalFlags.RUN_LAST,
            None,
            (GObject.TYPE_PYOBJECT,)
        )
    }

    def __init__(self):
        self.sorter = Gtk.CustomSorter()
        self.sorter.set_sort_func(self._sort_func)
        self.filter = Gtk.CustomFilter()
        self.filter.set_filter_func(self._filter_func)
        self.list_store = Gio.ListStore(item_type=Feed)
        self.sort_store = Gtk.SortListModel(
            model=self.list_store, sorter=self.sorter
        )
        self.confman = ConfManager()
        self.confman.connect(
                'gfeeds_show_empty_feeds_changed',
                lambda *_: self.invalidate_filter()
        )
        # Hiding read articles can result in empty feeds which should
        # be hidden
        self.confman.connect(
                'gfeeds_show_read_changed',
                lambda *_: self.invalidate_filter()
        )
        super().__init__(model=self.sort_store, filter=self.filter)

    def _sort_func(self, feed1: Feed, feed2: Feed, *_) -> int:
        return -1 if feed1.title.lower() < feed2.title.lower() else 1

    def invalidate_sort(self):
        self.sorter.set_sort_func(self._sort_func)

    def _filter_func(self, feed: Feed, *_) -> bool:
        res = True
        if not self.confman.conf['show_empty_feeds']:
            if self.confman.conf['show_read_items']:
                res = res and len(feed.items) > 0
            else:
                res = res and feed.unread_count > 0
        return res

    def invalidate_filter(self):
        self.filter.set_filter_func(self._filter_func)

    def empty(self):
        return self.list_store.remove_all()

    def add_feed(self, n_feed: Feed):
        self.list_store.append(n_feed)
        n_feed.connect(
            'empty_changed', lambda *_: self.invalidate_filter()
        )

    def remove_by_index(self, index: int):
        self.emit('item-removed', self.list_store[index])
        self.list_store.remove(index)

    def remove_feed(self, to_rm: Feed):
        for i, feed in enumerate(self.list_store):
            if feed.title == to_rm.title and feed.rss_link == to_rm.rss_link:
                self.remove_by_index(i)
                return

    def get_feed(self, identifier: str) -> Optional[Feed]:
        for f in self.list_store:
            if f.rss_link + f.title == identifier:
                return f
        return None
