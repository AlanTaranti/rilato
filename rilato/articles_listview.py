from typing import Any, Callable, Literal, Optional
from gi.repository import Gtk
from concurrent.futures import ThreadPoolExecutor
from rilato.feeds_manager import FeedsManager
from rilato.feed_item import FeedItem
from rilato.sidebar_row import SidebarRow


class CommonListScrolledWin(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__(
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
        )

        self.feedman = FeedsManager()
        self.articles_store = self.feedman.article_store

        self.fetch_image_thread_pool = ThreadPoolExecutor(
            max_workers=self.articles_store.confman.nconf.max_refresh_threads
        )

        # API bindings
        self.empty = self.articles_store.empty
        self.populate = self.articles_store.populate
        self.selected_feeds = self.articles_store.selected_feeds
        self.invalidate_filter = self.articles_store.invalidate_filter
        self.invalidate_sort = self.articles_store.invalidate_sort
        self.set_search_term = self.articles_store.set_search_term
        self.set_selected_feeds = self.articles_store.set_selected_feeds
        self.selected_feeds = self.articles_store.selected_feeds
        self.add_new_items = self.articles_store.add_new_items
        self.remove_items = self.articles_store.remove_items
        self.set_all_read_state = self.articles_store.set_all_read_state
        self.all_items_changed = self.articles_store.all_items_changed

    def shutdown_thread_pool(self):
        self.fetch_image_thread_pool.shutdown(wait=False, cancel_futures=True)

    def __del__(self):
        self.shutdown_thread_pool()


class ArticlesListView(CommonListScrolledWin):
    def __init__(self):
        super().__init__()

        # listview and factory
        self.factory = Gtk.SignalListItemFactory()
        self.factory.connect("setup", self._on_setup_listitem)
        self.factory.connect("bind", self._on_bind_listitem)
        self.selection = Gtk.SingleSelection.new(self.articles_store)
        self.selection.set_autoselect(False)
        self.list_view = Gtk.ListView.new(self.selection, self.factory)
        self.list_view.set_vscroll_policy(Gtk.ScrollablePolicy.NATURAL)

        self.list_view.get_style_context().add_class("navigation-sidebar")
        self.set_child(self.list_view)
        self.selection.connect("notify::selected-item", self.on_activate)

    def connect_activate(self, func):
        self.selection.connect(
            "notify::selected-item", lambda *_: func(self.selection.get_selected_item())
        )

    def get_selected(self) -> int:
        return self.selection.get_selected()

    def get_selected_item(self) -> FeedItem:
        return self.articles_store[self.get_selected()]

    def select_row(self, index):
        self.selection.select_item(index, True)

    # for both select next and prev; increment can be +1 or -1
    def __select_successive(self, increment: Literal[1, -1]):
        index = self.get_selected()
        if increment == -1 and index == 0:
            return
        if index == Gtk.INVALID_LIST_POSITION:
            index = -1 * increment  # so that 0 is selected
        self.select_row(index + increment)

    def select_next(self, *_):
        self.__select_successive(1)

    def select_prev(self, *_):
        self.__select_successive(-1)

    def on_activate(self, *_):
        feed_item = self.selection.get_selected_item()
        if not feed_item:
            return
        feed_item.read = True

    def _on_setup_listitem(self, _: Gtk.ListItemFactory, list_item: Gtk.ListItem):
        row_w = SidebarRow(self.fetch_image_thread_pool)
        list_item.set_child(row_w)
        # otherwise row gets garbage collected
        list_item.row_w = row_w  # type: ignore

    def _on_bind_listitem(self, _: Gtk.ListItemFactory, list_item: Gtk.ListItem):
        row_w: SidebarRow = list_item.get_child()  # type: ignore
        feed_item: FeedItem = list_item.get_item()  # type: ignore
        row_w.set_feed_item(feed_item)


class ArticlesListBox(CommonListScrolledWin):
    def __init__(self):
        super().__init__()

        self.listbox = Gtk.ListBox(
            vexpand=True,
            selection_mode=Gtk.SelectionMode.SINGLE,
            activate_on_single_click=True,
        )
        self.listbox.get_style_context().add_class("navigation-sidebar")
        self.listbox.bind_model(self.articles_store, self._create_row, None)
        self.set_child(self.listbox)

    def connect_activate(self, func: Callable[[Optional[FeedItem]], Any]):
        self.listbox.connect(
            "row-activated",
            lambda _, row, *__: func(row.get_child().feed_item) if row else func(None),
        )

    def _create_row(self, feed_item: FeedItem, *_) -> Gtk.Widget:
        row_w = SidebarRow(self.fetch_image_thread_pool)
        row_w.set_feed_item(feed_item)
        return row_w

    def get_selected_item(self):
        row = self.listbox.get_selected_row()
        if row:
            return row.get_child()
        return None

    def get_selected_index(self) -> int:
        row = self.listbox.get_selected_row()
        if not row:
            return -1
        index = row.get_index()
        if index is None:
            return 0
        return index

    # for both select next and prev; increment can be +1 or -1
    def __select_successive(self, increment: Literal[1, -1]):
        index = self.get_selected_index()
        if increment == -1 and index == 0:
            return
        if index < 0:
            index = -1 * increment  # so that 0 is selected
        target = self.listbox.get_row_at_index(index + increment)
        if not target:
            return
        self.listbox.select_row(target)
        target.activate()

    def select_next(self, *_):
        self.__select_successive(1)

    def select_prev(self, *_):
        self.__select_successive(-1)
