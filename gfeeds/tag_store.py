from typing import List, Union
from gi.repository import GObject, Gtk, Gio
from gfeeds.confManager import ConfManager


class TagObj(GObject.Object):
    def __init__(self, name: str):
        super().__init__()
        self.name = name


class TagStore(Gtk.SortListModel):
    __gsignals__ = {
        'item-removed': (
            GObject.SignalFlags.RUN_LAST,
            None,
            (GObject.TYPE_PYOBJECT,)
        )
    }

    def __init__(self):
        self.confman = ConfManager()
        self.sorter = Gtk.CustomSorter()
        self.sorter.set_sort_func(self._sort_func)
        self.list_store = Gio.ListStore(item_type=TagObj)
        super().__init__(model=self.list_store, sorter=self.sorter)
        self.populate()

    def populate(self):
        self.empty()
        for tag in self.confman.conf['tags']:
            self.list_store.append(TagObj(tag))

    def _sort_func(self, t1: TagObj, t2: TagObj, *_) -> int:
        return -1 if t1.name.lower() < t2.name.lower() else 1

    def empty(self):
        return self.list_store.remove_all()

    def add_tag(
            self, n_tag: Union[TagObj, str], target_feed_urls: List[str] = []
    ):
        if isinstance(n_tag, str):
            n_tag = TagObj(n_tag)
        if n_tag.name not in [t.name for t in self]:
            self.list_store.append(n_tag)
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
