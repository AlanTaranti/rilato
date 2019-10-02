from gi.repository import Gtk, Gdk
from .confManager import ConfManager
from .feeds_manager import FeedsManager
from .sidebar_row import GFeedsSidebarRow
from gettext import gettext as _


class GFeedsSidebarListBox(Gtk.ListBox):
    def __init__(self, parent_stack, **kwargs):
        super().__init__(**kwargs)
        self.search_terms = ''
        self.confman = ConfManager()
        self.parent_stack = parent_stack

        self.set_sort_from_confman()
        self.confman.connect(
            'gfeeds_new_first_changed',
            self.set_sort_from_confman
        )
        self.selected_feed = None
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
        self.longpress = Gtk.GestureLongPress.new(self)
        self.longpress.set_propagation_phase(Gtk.PropagationPhase.TARGET)
        self.longpress.set_touch_only(False)
        self.longpress.connect(
            'pressed',
            self.on_right_click,
            self
        )
        self.connect(
            'button-press-event',
            self.on_key_press_event
        )
        self.set_header_func(self.separator_header_func)

    def add(self, *args, **kwargs):
        super().add(*args, **kwargs)
        self.show_all()

    def separator_header_func(self, row, prev_row=None):
        if (
            prev_row != None and
            row.get_header() == None
        ):
            separator = Gtk.Separator(orientation = Gtk.Orientation.HORIZONTAL)
            row.set_header(separator)

    def on_show_read_changed(self, *args):
        self.invalidate_filter()

    def on_right_click(self, e_or_g, x, y, *args):
        row = self.get_row_at_y(y)
        if row:
            row.popover.popup()

    def on_key_press_event(self, what, event):
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3: # right click
            self.on_right_click(event, event.x, event.y)

    def change_filter(self, caller, n_filter):
        self.selected_feed = n_filter
        self.invalidate_filter()

    def gfeeds_sidebar_filter_func(self, row, data, notify_destroy):
        toret = False
        if not self.selected_feed:
            toret = True
        else:
            toret = row.feeditem.parent_feed == self.selected_feed
        return (
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
            self.add(GFeedsSidebarRow(i))
            self.show_all()

    def empty(self):
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
    def __init__(self, parent_stack, **kwargs):
        super().__init__(**kwargs)
        self.parent_stack = parent_stack
        self.listbox = GFeedsSidebarListBox(self.parent_stack)
        self.empty = self.listbox.empty
        self.populate = self.listbox.populate
        # self.set_size_request(360, 100)
        
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.add(self.listbox)

    def select_next_article(self, *args):
        target = None
        current_row = self.listbox.get_selected_row()
        if not current_row:
            target = self.listbox.get_row_at_index(0)
        else:
            target = self.listbox.get_row_at_index(
                current_row.get_index()+1
            )
        if target:
            self.listbox.select_row(target)
            self.listbox.emit('row-activated', target)

    def select_prev_article(self, *args):
        target = None
        current_row = self.listbox.get_selected_row()
        if not current_row:
            return
        else:
            target = self.listbox.get_row_at_index(
                current_row.get_index()-1
            )
        if target:
            self.listbox.select_row(target)
            self.listbox.emit('row-activated', target)

class GFeedsSidebar(Gtk.Stack):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.feedman = FeedsManager()
        self.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        self.scrolled_win = GFeedsSidebarScrolledWin(self)
        self.listbox = self.scrolled_win.listbox
        self.empty = self.scrolled_win.listbox.empty
        self.populate = self.scrolled_win.listbox.populate

        self.saved_items_scrolled_win = GFeedsSidebarScrolledWin(self)
        self.saved_items_listbox = self.saved_items_scrolled_win.listbox

        self.add_titled(self.scrolled_win, 'Feed', _('Feed'))
        self.child_set_property(
            self.scrolled_win,
            'icon-name',
            'application-rss+xml-symbolic'
        )
        self.add_titled(self.saved_items_scrolled_win, 'Saved', _('Saved'))
        self.child_set_property(
            self.saved_items_scrolled_win,
            'icon-name',
            'emblem-favorite-symbolic'
        )
        # self.set_size_request(360, 100)

        self.feedman.feeds_items.connect(
            'pop',
            lambda caller, obj: self.on_feeds_items_pop(obj)
        )
        self.feedman.feeds_items.connect(
            'append',
            lambda caller, obj: self.on_feeds_items_append(obj)
        )
        self.feedman.feeds_items.connect(
            'empty',
            lambda *args: self.listbox.empty()
        )
        self.feedman.saved_feeds_items.connect(
            'empty',
            lambda *args: self.saved_items_listbox.empty()
        )
        self.feedman.saved_feeds_items.connect(
            'append',
            lambda caller, obj: self.on_saved_feeds_items_append(obj)
        )

        self.feedman.feeds.connect(
            'pop',
            lambda caller, obj: self.on_feeds_pop(obj)
        )

    def on_feeds_pop(self, obj):
        if obj == self.listbox.selected_feed:
            self.listbox.selected_feed = None
            self.listbox.invalidate_filter()

    def set_search(self, search_terms):
        for lb in [self.listbox, self.saved_items_listbox]:
            lb.search_terms = search_terms
            lb.invalidate_filter()

    def on_saved_item_deleted(self, deleted_link):
        for row in self.listbox.get_children():
            if row.feeditem.link == deleted_link:
                with row.popover.save_btn.handler_block(
                    row.popover.save_btn_handler_id
                ):
                    row.popover.save_btn.set_active(False)
                break

    def select_next_article(self, *args):
        visible_child = self.get_visible_child()
        visible_child.select_next_article()

    def select_prev_article(self, *args):
        visible_child = self.get_visible_child()
        visible_child.select_prev_article()

    def on_feeds_items_pop(self, feeditem):
        for row in self.listbox.get_children():
            if row.feeditem == feeditem:
                self.listbox.remove(row)
                break

    def on_feeds_items_append(self, feeditem):
        self.listbox.add(
            GFeedsSidebarRow(feeditem)
        )

    def on_saved_feeds_items_append(self, feeditem):
        self.saved_items_listbox.add(
            GFeedsSidebarRow(feeditem, is_saved=True)
        )

    def on_saved_feeds_items_pop(self, feeditem):
        for row in self.saved_items_listbox.get_children():
            if row.feeditem == feeditem:
                self.listbox.remove(row)
                break
