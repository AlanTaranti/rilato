from gfeeds.feeds_view import FeedsViewScrolledWindow
from gi.repository import Gtk, Adw, GObject
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
from gfeeds.get_children import get_children
from functools import reduce
from operator import or_
from subprocess import Popen
from gfeeds.base_app import BaseWindow, AppShortcut


class GFeedsAppWindow(BaseWindow):
    def __init__(self):
        self.confman = ConfManager()
        self.feedman = FeedsManager()

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

        super().__init__(
            app_name='Feeds',
            icon_name='org.gabmus.gfeeds',
            shortcuts=[
                AppShortcut(
                    'F10', lambda *args: self.left_headerbar.menu_btn.popup()
                ),
                AppShortcut(
                    '<Control>r', self.feedman.refresh
                ),
                AppShortcut(
                    '<Control>f', lambda *args:
                        self.left_headerbar.search_btn.set_active(True)
                ),
                AppShortcut(
                    '<Control>j', self.sidebar.select_next_article
                ),
                AppShortcut(
                    '<Control>k', self.sidebar.select_prev_article
                ),
                AppShortcut(
                    '<Control>plus', self.webview.key_zoom_in
                ),
                AppShortcut(
                    '<Control>minus', self.webview.key_zoom_out
                ),
                AppShortcut(
                    '<Control>equal', self.webview.key_zoom_reset
                )
            ]
        )

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
            lambda caller, enabled: self.left_headerbar.search_btn.set_active(
                caller.get_search_mode()
            )
        )
        self.left_headerbar = GFeedsHeaderbarLeft(
            self.searchbar, self.leaflet
        )
        self.right_headerbar = GFeedsHeaderbarRight(
            self.webview, self.leaflet, self.on_back_button_clicked
        )
        self.left_headerbar.stack_switcher.set_stack(self.sidebar)
        self.left_headerbar.connect('squeeze', self.on_headerbar_squeeze)
        self.sidebar_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, hexpand=False
        )
        # self.sidebar_box.get_style_context().add_class('sidebar')
        self.sidebar_box.set_size_request(360, 100)
        self.sidebar_box.append(self.left_headerbar)
        self.sidebar_box.append(self.searchbar)
        self.sidebar_box.append(self.connection_bar)
        self.sidebar_box.append(self.errors_bar)
        self.webview_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, hexpand=True
        )
        self.webview_box.append(self.right_headerbar)
        self.webview_box.append(self.webview)

        self.stack_with_empty_state = StackWithEmptyState(self.sidebar)

        self.filter_flap = Adw.Flap(
            flap_position=Gtk.PackType.START,
            fold_policy=Adw.FlapFoldPolicy.ALWAYS,
            modal=True,
            reveal_flap=False,
            swipe_to_open=True, swipe_to_close=True
        )
        self.filter_sw = FeedsViewScrolledWindow(description=False, tags=True)
        self.filter_flap.get_style_context().add_class('background')
        self.stack_with_empty_state.get_style_context().add_class('sidebar')
        self.filter_flap.set_content(self.stack_with_empty_state)
        self.filter_flap.set_flap(self.filter_sw)
        # this activates the "All" feed filter. while this works it's kinda
        # hacky and needs a proper function
        self.feedman.connect(
            'feedmanager_refresh_start',
            lambda caller, msg:
            self.filter_sw.listbox.row_all_activate(
                skip=(msg == 'startup')
            )
        )
        self.left_headerbar.filter_btn.connect(
            'toggled', lambda btn:
                self.filter_flap.set_reveal_flap(btn.get_active())
        )
        self.filter_flap.connect(
            'notify::reveal-flap', lambda *args:
                self.left_headerbar.filter_btn.set_active(
                    self.filter_flap.get_reveal_flap()
                )
        )

        self.sidebar_box.append(self.filter_flap)
        self.leaflet.append(self.sidebar_box)
        self.leaflet.append(self.webview_box)
        self.leaflet.connect('notify::folded', self.on_main_leaflet_folded)

        self.bottom_bar = Adw.ViewSwitcherBar(stack=self.sidebar)
        self.bottom_bar.get_style_context().add_class('sidebar')
        self.sidebar_box.append(self.bottom_bar)

        # NOTE: this comment is deprecated
        # listening on the headerbar leaflet visible-child because of a bug in
        # libhandy that doesn't notify the correct child on the main leaflet
        self.leaflet.connect(
            'notify::visible-child', self.on_main_leaflet_folded
        )

        self.append(self.leaflet)
        self.on_main_leaflet_folded()

        self.confman.connect(
            'dark_mode_changed',
            lambda *args: self.set_dark_mode(self.confman.conf['dark_mode'])
        )
        self.set_dark_mode(self.confman.conf['dark_mode'])

    def present(self):
        super().present()
        self.set_default_size(
            self.confman.conf['windowsize']['width'],
            self.confman.conf['windowsize']['height']
        )

    def on_headerbar_squeeze(self, caller: GObject.Object, squeezed: bool):
        self.bottom_bar.set_reveal(squeezed)

    def emit_destroy(self, *args):
        self.emit('destroy')

    def on_destroy(self, *args):
        self.confman.conf['windowsize'] = {
            'width': self.get_width(),
            'height': self.get_height()
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
        self.confman.save_article_thumb_cache()

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
        for other_row in get_children(other_listbox):
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

    def on_back_button_clicked(self, *args):
        self.leaflet.set_visible_child(self.sidebar_box)
        self.on_main_leaflet_folded()
        self.sidebar.listbox.select_row(None)
        self.sidebar.saved_items_listbox.select_row(None)

    def on_main_leaflet_folded(self, *args):
        if self.leaflet.get_folded():
            self.right_headerbar.back_button.set_visible(True)
            self.left_headerbar.stack_switcher.set_visible(True)
        else:
            self.right_headerbar.back_button.set_visible(False)
            self.left_headerbar.stack_switcher.set_visible(False)
