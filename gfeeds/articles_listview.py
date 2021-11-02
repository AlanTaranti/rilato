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


class ArticlesListView(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__(
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            vscrollbar_policy=Gtk.PolicyType.AUTOMATIC
        )
        self.confman = ConfManager()

        # self.parent_stack = parent_stack

        # liststore stuff
        self.filter = Gtk.CustomFilter()
        self.filter.set_filter_func(self.filter_func)
        self.sorter = Gtk.CustomSorter()
        self.sorter.set_sort_func(self.sort_func)

        self.list_store = Gio.ListStore.new(FeedItemWrapper)

        self.filter_store = Gtk.FilterListModel.new(
            self.list_store, self.filter
        )
        self.sort_store = Gtk.SortListModel.new(
            self.filter_store, self.sorter
        )
        ## this is a chain: list_store contains the raw data,
        ## filter_store filters it and sort_store sorts it, then the listview
        ## is fed the last link in the chain via the selection object

        # listview and factory
        self.factory = Gtk.SignalListItemFactory()
        self.factory.connect('setup', self.on_setup_listitem)
        self.factory.connect('bind', self.on_bind_listitem)
        self.selection = Gtk.SingleSelection.new(self.sort_store)
        self.selection.set_autoselect(True)
        self.list_view = Gtk.ListView.new(self.selection, self.factory)

        self.list_view.get_style_context().add_class('sidebar')
        self.list_view.set_show_separators(True)
        self.list_view.set_single_click_activate(True)
        self.set_child(self.list_view)
        self.list_view.connect('activate', self.on_activate)

        self.selected_feeds = []
        self.__search_term = ''
        self.confman.connect(
            'gfeeds_show_read_changed', lambda *args: self.invalidate_filter()
        )
        self.confman.connect(
            'gfeeds_new_first_changed', lambda *args: self.invalidate_sort()
        )
        self.confman.connect(
            'gfeeds_filter_changed',
            self.change_filter
        )

    def change_filter(self, caller, n_filter):
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

    def set_search_term(self, term):
        self.__search_term = term.strip().lower()
        self.invalidate_filter()

    def set_selected_feeds(self, n_feeds_l):
        self.selected_feeds = n_feeds_l
        self.invalidate_filter()

    def invalidate_filter(self):
        self.filter.set_filter_func(self.filter_func)

    def invalidate_sort(self):
        self.sorter.set_sort_func(self.sort_func)

    def filter_func(self, item: FeedItemWrapper, *args) -> bool:
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

    def sort_func(
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

    def empty(self):
        self.list_store.remove_all()

    def get_selected(self) -> int:
        return self.selection.get_selected()

    def get_selected_item(self) -> FeedItemWrapper:
        return self.sort_store.get_item(self.get_selected())

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

    def add_new_items(self, feeditems_l):
        # self.parent_stack.set_main_visible(True)
        for i in feeditems_l:
            self.list_store.append(FeedItemWrapper(i))

    def remove_items(self, to_remove_l):
        for i in to_remove_l:
            found, pos = self.list_store.find_with_equal_func(
                FeedItemWrapper(i),
                lambda a, b: a.feed_item.link == b.feed_item.link
            )
            if found:
                self.list_store.remove(pos)

    def populate(self, feeditems_l):
        self.empty()  # TODO: review this API, doesn't make too much sense
        self.add_new_items(feeditems_l)

    def on_activate(self, lv, row_index):
        feed_item = self.sort_store.get_item(row_index).feed_item
        feed_item.set_read(True)
        # self.invalidate_filter() # maybe?
        # TODO

    def on_setup_listitem(self, factory: Gtk.ListItemFactory,
                          list_item: Gtk.ListItem):
        row_w = SidebarRow()
        list_item.set_child(row_w)
        list_item.row_w = row_w  # otherwise it gets garbage collected

    def on_bind_listitem(self, factory: Gtk.ListItemFactory,
                         list_item: Gtk.ListItem):
        row_w = list_item.get_child()
        row_w.set_feed_item(list_item.get_item())
