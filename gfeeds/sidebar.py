from gi.repository import Gtk, Gdk, GLib, Adw
from gettext import gettext as _
from gfeeds.confManager import ConfManager
from gfeeds.feeds_manager import FeedsManager
from gfeeds.sidebar_row import GFeedsSidebarRow
from gfeeds.accel_manager import add_mouse_button_accel, add_longpress_accel
from gfeeds.get_children import get_children
from gfeeds.articles_listview import ArticlesListView


class GFeedsSidebarListBox(Gtk.ListBox):
    def __init__(self, parent_stack):
        super().__init__(vexpand=True, show_separators=True)
        self.search_terms = ''
        self.confman = ConfManager()
        self.parent_stack = parent_stack

        self.set_sort_from_confman()
        self.confman.connect(
            'gfeeds_new_first_changed',
            self.set_sort_from_confman
        )
        self.selected_feeds = []
        self.set_filter_func(self.gfeeds_sidebar_filter_func, None, False)
        self.confman.connect(
            'gfeeds_filter_changed',
            self.change_filter
        )
        self.confman.connect(
            'gfeeds_show_read_changed',
            self.on_show_read_changed
        )

        # longpress & right click
        self.longpress = add_longpress_accel(
            self, self.on_right_click
        )
        self.rightclick = add_mouse_button_accel(
            self,
            lambda gesture, _, x, y:
                self.on_right_click(gesture, x, y)
                if gesture.get_current_button() == 3  # 3 is right click
                else None
        )

    def append(self, *args, **kwargs):
        super().append(*args, **kwargs)
        self.show()

    def on_show_read_changed(self, *args):
        self.invalidate_filter()

    def on_right_click(self, e_or_g, x, y, *args):
        row = self.get_row_at_y(y)
        if row:
            row.popover.popup()

    def on_key_press_event(self, what, event):
        # right click
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            self.on_right_click(event, event.x, event.y)

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

    def gfeeds_sidebar_filter_func(self, row, data, notify_destroy):
        toret = False
        if len(self.selected_feeds) <= 0:
            toret = True
        else:
            toret = row.feeditem.parent_feed.rss_link in self.selected_feeds
        return row.is_selected() or (
            toret and (
                self.confman.conf['show_read_items'] or
                not row.feeditem.read
            ) and (
                not self.search_terms or
                self.search_terms.lower() in row.feeditem.title.lower()
            )
        )

    def set_sort_from_confman(self, *args):
        if self.confman.conf['new_first']:
            self.set_sort_func(self.gfeeds_sort_new_first_func, None, False)
        else:
            self.set_sort_func(self.gfeeds_sort_old_first_func, None, False)

    def add_new_items(self, feeditems_l):
        self.parent_stack.set_main_visible(True)
        for i in feeditems_l:
            self.append(GFeedsSidebarRow(i))

    def empty(self, *args):
        while True:
            row = self.get_row_at_index(0)
            if row:
                self.remove(row)
            else:
                break

    def populate(self, feeditems_l):
        self.empty()
        self.add_new_items(feeditems_l)

    def gfeeds_sort_new_first_func(self, row1, row2, data, notify_destroy):
        return row1.feeditem.pub_date < row2.feeditem.pub_date

    def gfeeds_sort_old_first_func(self, row1, row2, data, notify_destroy):
        return row1.feeditem.pub_date > row2.feeditem.pub_date


class GFeedsSidebarScrolledWin(Gtk.ScrolledWindow):
    def __init__(self, parent_stack):
        super().__init__(
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            vscrollbar_policy=Gtk.PolicyType.AUTOMATIC
        )
        self.parent_stack = parent_stack
        self.listview = ArticlesListView()
        self.empty = self.listview.empty
        self.populate = self.listview.populate
        # self.set_size_request(360, 100)
        self.set_child(self.listview)

    def select_next_article(self, *args):
        index = self.listview.get_selected()
        if index == Gtk.INVALID_LIST_POSITION:
            return
        self.listview.select_row(index+1)

    def select_prev_article(self, *args):
        index = self.listview.get_selected()
        if index == Gtk.INVALID_LIST_POSITION:
            return
        self.listview.select_row(index-1)


class GFeedsSidebar(Adw.Bin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.feedman = FeedsManager()

        self.scrolled_win = GFeedsSidebarScrolledWin(self)
        self.listview = self.scrolled_win.listview
        self.empty = self.scrolled_win.listview.empty
        self.populate = self.scrolled_win.listview.populate

        self.set_child(self.scrolled_win)

        self.feedman.feeds_items.connect(
            'pop',
            lambda caller, obj: self.on_feeds_items_pop(obj)
        )
        self.feedman.feeds_items.connect(
            'append',
            lambda caller, obj: GLib.idle_add(
                self.on_feeds_items_append,
                obj,
                priority=GLib.PRIORITY_LOW)
        )
        self.feedman.feeds_items.connect(
            'extend',
            lambda caller, obj: GLib.idle_add(
                self.on_feeds_items_extend,
                caller,
                obj,
                priority=GLib.PRIORITY_LOW
            )
        )
        self.feedman.feeds_items.connect(
            'empty',
            lambda *args: self.listview.empty()
        )

        self.feedman.feeds.connect(
            'pop',
            lambda caller, obj: self.on_feeds_pop(obj)
        )

    def on_feeds_items_extend(self, caller, n_feeds_items_list):
        self.listview.add_new_items(n_feeds_items_list)

    def on_feeds_pop(self, obj):
        if obj.rss_link in self.listview.selected_feeds:
            n_selected_feeds = self.listview.selected_feeds
            n_selected_feeds.remove(obj.rss_link)
            self.listview.set_selected_feeds(n_selected_feeds)
        self.listview.remove_items(obj.items)

    def set_search(self, search_term):
        self.listview.set_search_term(search_term)

    def select_next_article(self, *args):
        self.scrolled_win.select_next_article()

    def select_prev_article(self, *args):
        self.scrolled_win.select_prev_article()

    def on_feeds_items_pop(self, feed_item):
        self.listview.remove_items([feed_item])

    def on_feeds_items_append(self, feed_item):
        self.listview.add_new_items([feed_item])
