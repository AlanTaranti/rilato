from gi.repository import Gtk, Handy, GObject
from typing import Callable
from gfeeds.confManager import ConfManager
from gfeeds.feeds_manager import FeedsManager
from gfeeds.sidebar import GFeedsSidebar
from gfeeds.headerbar import GFeedHeaderbar
from gfeeds.searchbar import GFeedsSearchbar
from gfeeds.suggestion_bar import (
    GFeedsConnectionBar,
    GFeedsErrorsBar
)
from gfeeds.webview import GFeedsWebView
from gfeeds.stack_with_empty_state import StackWithEmptyState


class GFeedsAppWindow(Handy.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.confman = ConfManager()
        self.feedman = FeedsManager()

        self.set_title('Feeds')
        self.set_icon_name('org.gabmus.gfeeds')

        self.sidebar = GFeedsSidebar()
        self.sidebar.listbox.connect(
            'row-activated',
            self.on_sidebar_row_activated
        )
        self.sidebar.saved_items_listbox.connect(
            'row-activated',
            self.on_sidebar_row_activated
        )

        self.webview = GFeedsWebView()

        separator = Gtk.Separator()
        separator.get_style_context().add_class('sidebar')

        leaflet_builder = Gtk.Builder.new_from_resource(
            '/org/gabmus/gfeeds/ui/gfeeds_leaflet.glade'
        )
        self.leaflet = leaflet_builder.get_object('leaflet')
        self.connection_bar = GFeedsConnectionBar()
        self.errors_bar = GFeedsErrorsBar(self)
        self.feedman.connect(
            'feedmanager_refresh_end',
            lambda *args: self.errors_bar.engage(
                self.feedman.errors,
                self.feedman.problematic_feeds
            )
        )
        self.searchbar = GFeedsSearchbar()
        self.searchbar.entry.connect(
            'changed',
            lambda entry: self.sidebar.set_search(entry.get_text())
        )
        self.searchbar.connect(
            'notify::search-mode-enabled',
            lambda caller, enabled:
                self.headerbar.search_btn.set_active(caller.get_search_mode())
        )
        self.sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.sidebar_box.set_size_request(360, 100)
        self.sidebar_box.pack_start(self.searchbar, False, False, 0)
        self.sidebar_box.pack_start(self.connection_bar, False, False, 0)
        self.sidebar_box.pack_start(self.errors_bar, False, False, 0)
        self.stack_with_empty_state = StackWithEmptyState(self.sidebar)
        self.sidebar_box.pack_start(self.stack_with_empty_state, True, True, 0)
        self.leaflet.add(self.sidebar_box)
        self.leaflet.add(separator)
        self.leaflet.add(self.webview)
        self.leaflet.child_set_property(separator, 'allow-visible', False)
        self.leaflet.connect('notify::folded', self.on_main_leaflet_folded)

        self.swipe_group = Handy.SwipeGroup()

        self.size_group_left = Gtk.SizeGroup(
            mode=Gtk.SizeGroupMode.HORIZONTAL
        )
        self.size_group_right = Gtk.SizeGroup(
            mode=Gtk.SizeGroupMode.HORIZONTAL
        )
        self.size_group_left.add_widget(self.sidebar_box)
        self.size_group_right.add_widget(self.webview)
        self.headerbar = GFeedHeaderbar(
            self.size_group_left,
            self.size_group_right,
            self.on_back_button_clicked,
            self.webview,
            self.searchbar
        )

        self.swipe_group.add_swipeable(self.leaflet)
        self.swipe_group.add_swipeable(self.headerbar.leaflet)

        self.headerbar.stack_switcher.set_stack(self.sidebar)
        self.headerbar.connect(
            'gfeeds_headerbar_squeeze',
            self.on_headerbar_squeeze
        )

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.bottom_bar = Handy.ViewSwitcherBar()
        self.bottom_bar.set_stack(self.sidebar)
        self.sidebar_box.pack_end(self.bottom_bar, False, False, 0)

        self.set_headerbar()

        # listening on the headerbar leaflet visible-child because of a bug in
        # libhandy that doesn't notify the correct child on the main leaflet
        self.headerbar.leaflet.connect(
            'notify::visible-child', self.on_main_leaflet_folded
        )

        self.add(self.main_box)
        self.main_box.pack_end(self.leaflet, True, True, 0)

        # Why this -52?
        # because every time a new value is saved, for some reason
        # it's the actual value +52 out of nowhere
        # this makes the window ACTUALLY preserve its old size
        self.resize(
            self.confman.conf['windowsize']['width']-52,
            self.confman.conf['windowsize']['height']-52
        )
        self.size_allocation = self.get_allocation()
        self.connect('size-allocate', self.update_size_allocation)
        self.on_main_leaflet_folded()

        # accel_group is for keyboard shortcuts
        self.accel_group = Gtk.AccelGroup()
        self.add_accel_group(self.accel_group)
        shortcuts_l = [
            {
                'combo': 'F10',
                'cb': lambda *args: self.headerbar.menu_btn.clicked()
            },
            {
                'combo': '<Control>r',
                'cb': self.feedman.refresh
            },
            {
                'combo': '<Control>f',
                'cb': lambda *args: self.headerbar.search_btn.set_active(True)
            },
            {
                'combo': '<Control>j',
                'cb': self.sidebar.select_next_article
            },
            {
                'combo': '<Control>k',
                'cb': self.sidebar.select_prev_article
            },
            {
                'combo': '<Control>plus',
                'cb': self.webview.key_zoom_in
            },
            {
                'combo': '<Control>minus',
                'cb': self.webview.key_zoom_out
            },
            {
                'combo': '<Control>equal',
                'cb': self.webview.key_zoom_reset
            }
        ]
        for s in shortcuts_l:
            self.add_accelerator(s['combo'], s['cb'])

    def on_headerbar_squeeze(self, caller: GObject.Object, squeezed: bool):
        self.bottom_bar.set_reveal(squeezed)

    def set_headerbar(self, *args):
        self.main_box.pack_start(self.headerbar, False, False, 0)
        self.headerbar.set_vexpand(False)

    def add_accelerator(self, shortcut: str, callback: Callable):
        if shortcut:
            key, mod = Gtk.accelerator_parse(shortcut)
            self.accel_group.connect(
                key, mod, Gtk.AccelFlags.VISIBLE, callback
            )

    def emit_destroy(self, *args):
        self.emit('destroy')

    def on_destroy(self, *args):
        self.confman.conf['windowsize'] = {
            'width': self.size_allocation.width,
            'height': self.size_allocation.height
        }
        # cleanup old read items
        feeds_items_links = [fi.link for fi in self.feedman.feeds_items]
        to_rm = []
        for ri in self.confman.conf['read_items']:
            if ri not in feeds_items_links:
                to_rm.append(ri)
        for ri in to_rm:
            self.confman.conf['read_items'].remove(ri)
        self.confman.save_conf()

    def on_sidebar_row_activated(
            self,
            listbox: Gtk.ListBox,
            row: Gtk.ListBoxRow
    ):
        row.popover.set_read(True)
        other_listbox = (
            self.sidebar.listbox
            if listbox == self.sidebar.saved_items_listbox
            else self.sidebar.saved_items_listbox
        )
        for other_row in other_listbox:
            if other_row.feeditem.link == row.feeditem.link:
                other_row.popover.set_read(True)
                break
        self.webview.load_feeditem(row.feeditem)
        self.headerbar.set_article_title(
            row.feeditem.title
        )
        self.headerbar.share_btn.set_sensitive(True)
        self.headerbar.open_externally_btn.set_sensitive(True)
        self.leaflet.set_visible_child(self.webview)
        self.headerbar.leaflet.set_visible_child(
            self.headerbar.right_headerbar
        )
        self.on_main_leaflet_folded()
        listbox.invalidate_filter()
        other_listbox.invalidate_filter()

    def on_main_leaflet_folded(self, *args):
        # target = None
        # other = None
        if self.leaflet.get_folded():
            # target = self.headerbar.leaflet.get_visible_child()
            self.headerbar.back_button.show()
            self.headerbar.stack_switcher.set_no_show_all(False)
            self.headerbar.stack_switcher.show()
            self.headerbar.squeezer.set_child_enabled(
                self.headerbar.stack_switcher, True
            )
        else:
            self.headerbar.back_button.hide()
            self.headerbar.stack_switcher.set_no_show_all(True)
            self.headerbar.stack_switcher.hide()
            self.headerbar.squeezer.set_child_enabled(
                self.headerbar.stack_switcher, False
            )
        # self.headerbar.headergroup.set_focus(target)

    def on_back_button_clicked(self, *args):
        self.leaflet.set_visible_child(self.sidebar_box)
        self.on_main_leaflet_folded()
        self.sidebar.listbox.select_row(None)
        self.sidebar.saved_items_listbox.select_row(None)

    def update_size_allocation(self, *args):
        self.size_allocation = self.get_allocation()
