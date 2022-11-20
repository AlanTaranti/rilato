from gettext import ngettext
from functools import reduce
from typing import Optional
from gfeeds.filter_view import FilterView
from gfeeds.feed_item import FeedItem
from gfeeds.stack_with_empty_state import StackWithEmptyState
from operator import or_
from subprocess import Popen
from gi.repository import GObject, Gtk, Adw, Gio
from gfeeds.sidebar import GFeedsSidebar
from gfeeds.webview import GFeedsWebView
from gfeeds.headerbar import LeftHeaderbar, RightHeaderbar
from gfeeds.confManager import ConfManager
from gfeeds.feeds_manager import FeedsManager


@Gtk.Template(resource_path='/org/gabmus/gfeeds/ui/main_leaflet.ui')
class MainLeaflet(Adw.Bin):
    __gtype_name__ = 'MainLeaflet'
    left_box = Gtk.Template.Child()
    right_box = Gtk.Template.Child()
    leaflet = Gtk.Template.Child()
    connection_bar: Gtk.InfoBar = Gtk.Template.Child()
    left_headerbar: LeftHeaderbar = Gtk.Template.Child()
    filter_view: FilterView = Gtk.Template.Child()
    searchbar: Gtk.SearchBar = Gtk.Template.Child()
    searchbar_entry: Gtk.SearchEntry = Gtk.Template.Child()
    filter_flap: Adw.Flap = Gtk.Template.Child()
    sidebar_stack: StackWithEmptyState = Gtk.Template.Child()
    sidebar: GFeedsSidebar = Gtk.Template.Child()
    webview: GFeedsWebView = Gtk.Template.Child()
    right_headerbar: RightHeaderbar = Gtk.Template.Child()

    def __init__(self):
        super().__init__()
        self.confman = ConfManager()
        self.feedman = FeedsManager()

        self.sidebar.listview_sw.connect_activate(
            self.on_sidebar_row_activated
        )
        self.filter_flap.bind_property(
            'reveal-flap', self.left_headerbar.filter_btn, 'active',
            GObject.BindingFlags.BIDIRECTIONAL
        )

        self.confman.connect(
            'gfeeds_filter_changed', self.on_filter_changed
        )
        self.searchbar_entry.connect(
            'changed',
            lambda entry: self.sidebar.set_search(entry.get_text())
        )
        self.searchbar.bind_property(
            'search-mode-enabled', self.left_headerbar.search_btn,
            'active', GObject.BindingFlags.BIDIRECTIONAL
        )

        self.feedman.connect(
            'feedmanager_refresh_end', self.on_refresh_end
        )
        self.feedman.connect(
            'feedmanager_online_changed',
            lambda _, value: self.connection_bar.set_revealed(not value)
        )

        self.on_leaflet_folded()

    def on_filter_changed(self, *_):
        self.left_headerbar.filter_btn.set_active(False)
        # reset vertical scroll position to 0
        adjustment = self.sidebar.listview_sw.get_vadjustment()
        adjustment.set_value(0)
        self.sidebar.listview_sw.set_vadjustment(adjustment)

    @Gtk.Template.Callback()
    def on_leaflet_folded(self, *args):
        rh = self.right_headerbar.right_headerbar
        lh = self.left_headerbar.left_headerbar
        if self.leaflet.get_folded():
            self.right_headerbar.back_btn.set_visible(True)
            rh.set_show_start_title_buttons(True)
            rh.set_show_end_title_buttons(True)
            lh.set_show_start_title_buttons(True)
            lh.set_show_end_title_buttons(True)
        else:
            self.right_headerbar.back_btn.set_visible(False)
            rh.set_show_start_title_buttons(False)
            rh.set_show_end_title_buttons(True)
            lh.set_show_start_title_buttons(True)
            lh.set_show_end_title_buttons(False)

    @Gtk.Template.Callback()
    def on_back_btn_clicked(self, *_):
        self.leaflet.set_visible_child(self.left_box)
        self.on_leaflet_folded()

    def on_view_mode_change(self, target):
        self.right_headerbar.on_view_mode_change(target)
        self.webview.change_view_mode(target)

    def on_refresh_end(self, *args):
        self.left_headerbar.errors_btn.set_visible(
            len(self.feedman.errors) > 0
        )
        self.sidebar.listview_sw.all_items_changed()
        self.sidebar.loading_revealer.set_running(False)
        if (
                self.confman.conf['notify_new_articles'] and
                not self.get_root().is_active() and  # window is not focused
                self.feedman.new_items_num > 0
        ):
            notif_text = ngettext(
                '{0} new article', '{0} new articles',
                self.feedman.new_items_num
            ).format(self.feedman.new_items_num)
            notif = Gio.Notification.new(notif_text)
            notif.set_icon(Gio.ThemedIcon.new(
                'org.gabmus.gfeeds-symbolic'
            ))
            self.get_root().app.send_notification('new_articles', notif)

    def on_sidebar_row_activated(self, feed_item: Optional[FeedItem]):
        self.feedman.article_store.set_selected_article(feed_item)
        if not feed_item:
            return
        feed_item.read = True
        if (
                self.confman.conf['open_youtube_externally'] and
                reduce(or_, [
                    f'://{pfx}' in feed_item.link  # type: ignore
                    for pfx in [
                        p + 'youtube.com'
                        for p in ('', 'www.', 'm.')
                    ]
                ])
        ):
            cmd_parts = [
                self.confman.conf['media_player'], f'"{feed_item.link}"'
            ]
            if self.confman.is_flatpak:
                cmd_parts.insert(0, 'flatpak-spawn --host')
            cmd = ' '.join(cmd_parts)
            Popen(cmd, shell=True)
            return
        self.webview.load_feeditem(feed_item)
        self.right_headerbar.set_article_title(
            feed_item.title
        )
        self.right_headerbar.extra_menu_btn.set_sensitive(True)
        self.leaflet.set_visible_child(self.right_box)
        self.on_leaflet_folded()
        self.sidebar.listview_sw.invalidate_filter()
        feed_item.emit('changed', '')
