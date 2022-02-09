from gi.repository import GObject, Gtk, Gio
from gfeeds.rss_parser import Feed


class FeedStore(Gtk.SortListModel):
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
        self.list_store = Gio.ListStore(item_type=Feed)
        super().__init__(model=self.list_store, sorter=self.sorter)

    def _sort_func(self, feed1: Feed, feed2: Feed, *_) -> int:
        return -1 if feed1.title.lower() < feed2.title.lower() else 1

    def invalidate_sort(self):
        self.sorter.set_sort_func(self._sort_func)

    def empty(self):
        return self.list_store.remove_all()

    def add_feed(self, n_feed: Feed):
        self.list_store.append(n_feed)

    def remove_by_index(self, index: int):
        self.emit('item-removed', self.list_store[index])
        self.list_store.remove(index)

    def remove_feed(self, to_rm: Feed):
        for i, feed in enumerate(self.list_store):
            if feed.title == to_rm.title and feed.rss_link == to_rm.rss_link:
                self.remove_by_index(i)
                return
