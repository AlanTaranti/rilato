from gi.repository import Gtk
from concurrent.futures import ThreadPoolExecutor
from gfeeds.feeds_manager import FeedsManager
from gfeeds.rss_parser import FeedItem
from gfeeds.sidebar_row import SidebarRow


class CommonListScrolledWin(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__(
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            vscrollbar_policy=Gtk.PolicyType.AUTOMATIC
        )

        self.feedman = FeedsManager()
        self.articles_store = self.feedman.article_store

        self.fetch_image_thread_pool = ThreadPoolExecutor(
            max_workers=self.articles_store.confman.conf[
                'max_refresh_threads'
            ]
        )

        # API bindings
        self.articles_store._bind_api(self)

    def shutdown_thread_pool(self):
        self.fetch_image_thread_pool.shutdown(wait=False, cancel_futures=True)

    def __del__(self):
        self.shutdown_thread_pool()
        super().__del__()


class ArticlesListView(CommonListScrolledWin):
    def __init__(self):
        super().__init__()

        # listview and factory
        self.factory = Gtk.SignalListItemFactory()
        self.factory.connect('setup', self._on_setup_listitem)
        self.factory.connect('bind', self._on_bind_listitem)
        self.selection = Gtk.SingleSelection.new(self.articles_store)
        self.selection.set_autoselect(False)
        self.list_view = Gtk.ListView.new(self.selection, self.factory)
        self.list_view.set_vscroll_policy(Gtk.ScrollablePolicy.NATURAL)

        self.list_view.get_style_context().add_class('navigation-sidebar')
        self.set_child(self.list_view)
        self.selection.connect('notify::selected-item', self.on_activate)

    def connect_activate(self, func):
        self.selection.connect(
            'notify::selected-item',
            lambda caller, feed_item, *args:
                func(self.selection.get_selected_item())
        )

    def get_selected(self) -> int:
        return self.selection.get_selected()

    def get_selected_item(self) -> FeedItem:
        return self.articles_store.get_item(self.get_selected())

    def select_row(self, index):
        self.selection.select_item(index, True)

    def select_next(self, *args):
        index = self.get_selected()
        if index == Gtk.INVALID_LIST_POSITION:
            return self.select_row(0)
        # if index > ??? num_rows?:
        #     return
        self.select_row(index+1)

    def select_prev(self, *args):
        index = self.get_selected()
        if index == Gtk.INVALID_LIST_POSITION:
            return self.select_row(0)
        if index == 0:
            return
        self.select_row(index-1)

    def on_activate(self, *args):
        feed_item = self.selection.get_selected_item()
        if not feed_item:
            return
        feed_item.read = True

    def _on_setup_listitem(
            self, factory: Gtk.ListItemFactory, list_item: Gtk.ListItem
    ):
        row_w = SidebarRow(self.fetch_image_thread_pool)
        list_item.set_child(row_w)
        list_item.row_w = row_w  # otherwise it gets garbage collected

    def _on_bind_listitem(
            self, factory: Gtk.ListItemFactory, list_item: Gtk.ListItem
    ):
        row_w = list_item.get_child()
        row_w.set_feed_item(list_item.get_item())


class ArticlesListBox(CommonListScrolledWin):
    def __init__(self):
        super().__init__()

        self.listbox = Gtk.ListBox(
            vexpand=True, selection_mode=Gtk.SelectionMode.SINGLE,
            activate_on_single_click=True
        )
        self.listbox.get_style_context().add_class('navigation-sidebar')
        self.listbox.bind_model(self.articles_store, self._create_row, None)
        self.set_child(self.listbox)

    def connect_activate(self, func):
        self.listbox.connect(
            'row-activated',
            lambda lb, row, *args:
                func(row.get_child().feed_item)
                if row else func(None)
        )

    def _create_row(
            self, feed_item: FeedItem, *args
    ) -> Gtk.Widget:
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

    def select_next(self, *args):
        index = self.get_selected_index()
        if index < 0:
            index = -1  # so that 0 is selected
        target = self.listbox.get_row_at_index(index+1)
        if not target:
            return
        self.listbox.select_row(target)
        target.activate()

    def select_prev(self, *args):
        index = self.get_selected_index()
        if index <= 0:
            index = 1  # so that 0 is selected
        target = self.listbox.get_row_at_index(index-1)
        if not target:
            return
        self.listbox.select_row(target)
        target.activate()
