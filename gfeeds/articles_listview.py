from gi.repository import Gtk, GObject, Gio
from gfeeds.rss_parser import FeedItem
from gfeeds.confManager import ConfManager
from gfeeds.sidebar_row import SidebarRow


class FeedItemWrapper(GObject.Object):
    __gsignals__ = {
        'changed': (
            GObject.SignalFlags.RUN_FIRST, None, (str,)
        )
    }

    def __init__(self, feed_item: FeedItem):
        super().__init__()
        self.feed_item = feed_item

    def emit_changed(self):
        self.emit('changed', '')


class ArticlesListModel(Gtk.SortListModel):
    def __init__(self):
        self.selected_feeds = []
        self.__search_term = ''

        ## this is a chain: list_store contains the raw data,
        ## filter_store filters it and sort_store sorts it, then the listview
        ## is fed the last link in the chain via the selection object
        self.filter = Gtk.CustomFilter()
        self.filter.set_filter_func(self._filter_func)
        self.sorter = Gtk.CustomSorter()
        self.sorter.set_sort_func(self._sort_func)
        self.list_store = Gio.ListStore(item_type=FeedItemWrapper)
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

    def _filter_func(self, item: FeedItemWrapper, *args) -> bool:
        res = True
        if len(self.selected_feeds) > 0:
            res = item.feed_item.parent_feed.rss_link in self.selected_feeds
        if not self.confman.conf['show_read_items']:
            res = res and (not item.feed_item.read)
        if self.__search_term:
            res = res and (
                self.__search_term in item.feed_item.title.lower()
            )
        return res

    def _sort_func(
            self, item1: FeedItemWrapper, item2: FeedItemWrapper, *args
    ) -> int:
        # item1 first -> -1
        # item2 first -> +1
        # equal (unused) -> 0
        if self.confman.conf['new_first']:
            return (
                -1 if item1.feed_item.pub_date > item2.feed_item.pub_date
                else 1
            )
        return (
            -1 if item1.feed_item.pub_date < item2.feed_item.pub_date
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
            self.list_store.append(FeedItemWrapper(i))

    def populate(self, feeditems_l):
        self.empty()  # TODO: review this API, doesn't make too much sense
        self.add_new_items(feeditems_l)

    def remove_items(self, to_remove_l):
        for i in to_remove_l:
            found, pos = self.list_store.find_with_equal_func(
                FeedItemWrapper(i),
                lambda a, b: a.feed_item.link == b.feed_item.link
            )
            if found:
                self.list_store.remove(pos)

    def set_search_term(self, term):
        self.__search_term = term.strip().lower()
        self.invalidate_filter()

    def set_selected_feeds(self, n_feeds_l):
        self.selected_feeds = n_feeds_l
        self.invalidate_filter()


class ArticlesListView(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__(
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            vscrollbar_policy=Gtk.PolicyType.AUTOMATIC
        )

        self.articles_store = ArticlesListModel()

        # listview and factory
        self.factory = Gtk.SignalListItemFactory()
        self.factory.connect('setup', self._on_setup_listitem)
        self.factory.connect('bind', self._on_bind_listitem)
        self.selection = Gtk.SingleSelection.new(self.articles_store)
        self.selection.set_autoselect(True)
        self.list_view = Gtk.ListView.new(self.selection, self.factory)

        self.list_view.get_style_context().add_class('navigation-sidebar')
        self.list_view.set_single_click_activate(True)
        self.set_child(self.list_view)
        self.list_view.connect('activate', self.on_activate)

        # API bindings
        self.empty = self.articles_store.empty
        self.populate = self.articles_store.populate
        self.selected_feeds = self.articles_store.selected_feeds
        self.invalidate_filter = self.articles_store.invalidate_filter
        self.invalidate_sort = self.articles_store.invalidate_sort
        self.set_search_term = self.articles_store.set_search_term
        self.set_selected_feeds = self.articles_store.selected_feeds
        self.add_new_items = self.articles_store.add_new_items
        self.remove_items = self.articles_store.remove_items

    def connect_activate(self, func):
        self.list_view.connect(
            'activate',
            lambda lv, index, *args:
                func(self.articles_store.get_item(index))
        )

    def get_selected(self) -> int:
        return self.selection.get_selected()

    def get_selected_item(self) -> FeedItemWrapper:
        return self.articles_store.get_item(self.get_selected())

    def select_row(self, index):
        self.selection.select_item(index, True)
        self.list_view.emit('activate', index)

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

    def on_activate(self, lv, row_index):
        feed_item = self.articles_store.get_item(row_index).feed_item
        feed_item.set_read(True)
        # self.invalidate_filter() # maybe?
        # TODO

    def _on_setup_listitem(self, factory: Gtk.ListItemFactory,
                          list_item: Gtk.ListItem):
        row_w = SidebarRow()
        list_item.set_child(row_w)
        list_item.row_w = row_w  # otherwise it gets garbage collected

    def _on_bind_listitem(self, factory: Gtk.ListItemFactory,
                         list_item: Gtk.ListItem):
        row_w = list_item.get_child()
        row_w.set_feed_item(list_item.get_item())


class ArticlesListBox(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__(
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            vscrollbar_policy=Gtk.PolicyType.AUTOMATIC
        )

        self.articles_store = ArticlesListModel()

        self.listbox = Gtk.ListBox(
            vexpand=True, selection_mode=Gtk.SelectionMode.SINGLE,
            activate_on_single_click=True
        )
        self.listbox.get_style_context().add_class('navigation-sidebar')
        self.listbox.bind_model(self.articles_store, self._create_row, None)
        self.set_child(self.listbox)

        # API bindings
        self.empty = self.articles_store.empty
        self.populate = self.articles_store.populate
        self.selected_feeds = self.articles_store.selected_feeds
        self.invalidate_filter = self.articles_store.invalidate_filter
        self.invalidate_sort = self.articles_store.invalidate_sort
        self.set_search_term = self.articles_store.set_search_term
        self.set_selected_feeds = self.articles_store.selected_feeds
        self.add_new_items = self.articles_store.add_new_items
        self.remove_items = self.articles_store.remove_items

    def connect_activate(self, func):
        self.listbox.connect(
            'row-activated',
            lambda lb, row, *args:
                func(row.get_child().feed_item_wrapper)
                if row else func(None)
        )

    def _create_row(self, feed_item_wrapper: FeedItemWrapper, *args) -> Gtk.Widget:
        row_w = SidebarRow()
        row_w.set_feed_item(feed_item_wrapper)
        return row_w

    def get_selected_item(self):
        row = self.listbox.get_selected_row()
        if row:
            return row.get_child().feed_item_wrapper
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
