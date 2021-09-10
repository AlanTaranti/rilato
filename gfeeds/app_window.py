from gi.repository import Gtk, Adw, GObject
from typing import Callable
from gfeeds.confManager import ConfManager
from gfeeds.feeds_manager import FeedsManager
from gfeeds.sidebar import GFeedsSidebar
from gfeeds.headerbar import GFeedsHeaderbarLeft, GFeedsHeaderbarRight
from gfeeds.searchbar import GFeedsSearchbar
from gfeeds.suggestion_bar import (
    GFeedsConnectionBar,
    GFeedsErrorsBar
)
from gfeeds.webview import GFeedsWebView
from gfeeds.stack_with_empty_state import StackWithEmptyState
from gfeeds.accel_manager import add_accelerators
from functools import reduce
from operator import or_
from subprocess import Popen


class GFeedsAppWindow(Adw.ApplicationWindow):
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

        # separator = Gtk.Separator()
        # separator.get_style_context().add_class('sidebar')

        leaflet_builder = Gtk.Builder.new_from_resource(
            '/org/gabmus/gfeeds/ui/gfeeds_leaflet.ui'
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
                self.left_headerbar.search_btn.set_active(caller.get_search_mode())
        )
        self.left_headerbar = GFeedsHeaderbarLeft(
            self.on_back_button_clicked,
            self.searchbar
        )
        self.right_headerbar = GFeedsHeaderbarRight(self.webview)
        self.left_headerbar.stack_switcher.set_stack(self.sidebar)
        self.left_headerbar.connect(
            'gfeeds_headerbar_squeeze',
            self.on_headerbar_squeeze
        )
        self.sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.sidebar_box.get_style_context().add_class('sidebar')
        self.sidebar_box.set_size_request(360, 100)
        self.sidebar_box.append(self.left_headerbar)
        self.sidebar_box.append(self.searchbar)
        self.sidebar_box.append(self.connection_bar)
        self.sidebar_box.append(self.errors_bar)
        self.webview_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.webview_box.append(self.right_headerbar)
        self.webview_box.append(self.webview)
        self.stack_with_empty_state = StackWithEmptyState(self.sidebar)
        self.sidebar_box.append(self.stack_with_empty_state)
        self.leaflet.append(self.sidebar_box)
        # self.leaflet.append(separator)
        self.leaflet.append(self.webview_box)
        # self.leaflet.child_set_property(separator, 'allow-visible', False)
        self.leaflet.connect('notify::folded', self.on_main_leaflet_folded)

        self.main_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, hexpand=True, vexpand=True
        )

        self.bottom_bar = Adw.ViewSwitcherBar()
        self.bottom_bar.set_stack(self.sidebar)
        self.sidebar_box.append(self.bottom_bar)

        # NOTE: this comment is deprecated
        # listening on the headerbar leaflet visible-child because of a bug in
        # libhandy that doesn't notify the correct child on the main leaflet
        self.leaflet.connect(
            'notify::visible-child', self.on_main_leaflet_folded
        )

        self.main_box.append(self.leaflet)
        self.set_child(self.main_box)

        self.set_default_size(
            self.confman.conf['windowsize']['width'],
            self.confman.conf['windowsize']['height']
        )
        self.size_allocation = self.get_allocation()
        self.on_main_leaflet_folded()

        add_accelerators(
            self,
            [
                {
                    'combo': 'F10',
                    'cb': lambda *args:
                        self.left_headerbar.menu_btn.podown()
                        if self.left_headerbar.menu_popover.get_visible()
                        else self.left_headerbar.menu_btn.popup()
                },
                {
                    'combo': '<Control>r',
                    'cb': self.feedman.refresh
                },
                {
                    'combo': '<Control>f',
                    'cb': lambda *args: self.left_headerbar.search_btn.set_active(True)
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
        )

        self.confman.connect('gfeeds_dark_mode_changed', self.on_dark_mode_changed)

    def present(self, *args, **kwargs):
        super().present(*args, **kwargs)
        self.on_dark_mode_changed()

    def on_dark_mode_changed(self, *args):
        Gtk.Settings.get_default().set_property(
            'gtk-application-prefer-dark-theme',
            self.confman.conf['dark_mode']
        )

    def on_headerbar_squeeze(self, caller: GObject.Object, squeezed: bool):
        self.bottom_bar.set_reveal(squeezed)

    def emit_destroy(self, *args):
        self.emit('destroy')

    def on_destroy(self, *args):
        alloc = self.get_allocation()
        self.confman.conf['windowsize'] = {
            'width': alloc.width,
            'height': alloc.height
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
        if (
                self.confman.conf['open_youtube_externally'] and
                reduce(or_, [
                    f'://{pfx}' in row.feeditem.link
                    for pfx in [
                        p + 'youtube.com'
                        for p in ('', 'www.', 'm.')
                    ]
                ])
        ):
            cmd_parts = [
                self.confman.conf["media_player"],
                row.feeditem.link
            ]
            if self.confman.is_flatpak:
                cmd_parts.insert(0, 'flatpak-spawn --host')
            cmd = ' '.join(cmd_parts)
            Popen(
                cmd,
                shell=True
            )
            return
        self.webview.load_feeditem(row.feeditem)
        self.right_headerbar.set_article_title(
            row.feeditem.title
        )
        self.right_headerbar.share_btn.set_sensitive(True)
        self.right_headerbar.open_externally_btn.set_sensitive(True)
        self.leaflet.set_visible_child(self.webview_box)
        self.on_main_leaflet_folded()
        listbox.invalidate_filter()
        other_listbox.invalidate_filter()

    def on_main_leaflet_folded(self, *args):
        # target = None
        # other = None
        if self.leaflet.get_folded():
            # target = self.headerbar.leaflet.get_visible_child()
            self.left_headerbar.back_button.show()
            self.left_headerbar.stack_switcher.set_visible(True)
            self.left_headerbar.stack_switcher.show()
            # self.left_headerbar.squeezer.set_child_enabled(
            #     self.left_headerbar.stack_switcher, True
            # )
        else:
            self.left_headerbar.back_button.hide()
            self.left_headerbar.stack_switcher.set_visible(False)
            self.left_headerbar.stack_switcher.hide()
            # self.left_headerbar.squeezer.set_child_enabled(
            #     self.left_headerbar.stack_switcher, False
            # )
        # self.headerbar.headergroup.set_focus(target)

    def on_back_button_clicked(self, *args):
        self.leaflet.set_visible_child(self.sidebar_box)
        self.on_main_leaflet_folded()
        self.sidebar.listbox.select_row(None)
        self.sidebar.saved_items_listbox.select_row(None)
