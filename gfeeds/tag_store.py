from typing import List, Union
from gi.repository import GObject, Gtk, Gio
from gfeeds.confManager import ConfManager
from gfeeds.feed import Feed


class TagObj(GObject.Object):
    __gsignals__ = {
        'empty_changed': (
            GObject.SignalFlags.RUN_FIRST, GObject.TYPE_NONE, ()
        )
    }

    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.__unread_count = 0

    @GObject.Property(type=int)
    def unread_count(self) -> int:  # type: ignore
        return self.__unread_count

    @unread_count.setter
    def unread_count(self, c: int):
        self.__unread_count = c

    def increment_unread_count(self, v: int):
        prev = self.unread_count
        self.unread_count += v
        if self.__unread_count == 0 and prev > 0:
            self.emit('empty_changed')
        elif self.__unread_count > 0 and prev == 0:
            self.emit('empty_changed')


class TagStore(Gtk.FilterListModel):
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
        self.list_store = Gio.ListStore(item_type=TagObj)
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
        self.populate()

    def populate(self):
        self.empty()
        for tag in self.confman.nconf.tags:
            n_tag = TagObj(tag)
            self.list_store.append(n_tag)
            n_tag.connect(
                'empty_changed', lambda *_: self.invalidate_filter()
            )

    def _sort_func(self, t1: TagObj, t2: TagObj, *_) -> int:
        return -1 if t1.name.lower() < t2.name.lower() else 1

    def empty(self):
        return self.list_store.remove_all()

    def add_tag(
            self, n_tag_: Union[TagObj, str], target_feeds: List[Feed] = []
    ):
        n_tag = TagObj(n_tag_) if isinstance(n_tag_, str) else n_tag_
        existing_tag = self.get_tag(n_tag.name)
        if existing_tag:
            n_tag = existing_tag
        else:
            self.list_store.append(n_tag)

        target_feed_urls = []
        for feed in target_feeds:
            target_feed_urls.append(feed.rss_link)
            if n_tag not in feed.tags:
                feed.tags.append(n_tag)
                n_tag.unread_count += feed.unread_count
        n_tag.connect(
            'empty_changed', lambda *_: self.invalidate_filter()
        )

        self.confman.add_tag(n_tag.name, target_feed_urls)

    def remove_by_index(self, index: int):
        to_rm = self.list_store[index]
        self.emit('item-removed', to_rm)
        self.list_store.remove(index)
        self.confman.delete_tag(to_rm.name)

    def remove_tag(self, tag: str):
        for i, tag_o in enumerate(self.list_store):
            if tag == tag_o.name:
                self.remove_by_index(i)
                return

    def _filter_func(self, item: TagObj, *_) -> bool:
        if not self.confman.nconf.show_empty_feeds and \
                not self.confman.nconf.show_read_items:
            return item.unread_count > 0
        return True

    def invalidate_filter(self):
        self.filter.set_filter_func(self._filter_func)

    def get_tag(self, tag: str):
        for t in self.list_store:
            if t.name == tag:
                return t
        return None
