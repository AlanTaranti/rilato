from gettext import ngettext
from functools import reduce
from gfeeds.feeds_view import FeedsViewScrolledWindow
from gfeeds.rss_parser import FeedItem
from gfeeds.stack_with_empty_state import StackWithEmptyState
from operator import or_
from subprocess import Popen
from gi.repository import Gtk, Adw, Gio
from gfeeds.sidebar import GFeedsSidebar
from gfeeds.suggestion_bar import GFeedsConnectionBar
from gfeeds.webview import GFeedsWebView
from gfeeds.searchbar import GFeedsSearchbar
from gfeeds.headerbar import LeftHeaderbar, RightHeaderbar
from gfeeds.confManager import ConfManager
from gfeeds.feeds_manager import FeedsManager


@Gtk.Template(resource_path='/org/gabmus/gfeeds/ui/main_leaflet.ui')
class MainLeaflet(Adw.Bin):
    __gtype_name__ = 'MainLeaflet'
    left_box = Gtk.Template.Child()
    right_box = Gtk.Template.Child()
    leaflet = Gtk.Template.Child()

    def __init__(self):
        super().__init__()
        self.confman = ConfManager()
        self.feedman = FeedsManager()

        self.sidebar = GFeedsSidebar()
        self.sidebar_stack = StackWithEmptyState(self.sidebar)
        self.filter_flap = Adw.Flap(
            flap_position=Gtk.PackType.START,
            fold_policy=Adw.FlapFoldPolicy.ALWAYS,
            modal=True,
            reveal_flap=False,
            swipe_to_open=True, swipe_to_close=True
        )
        self.filter_sw = FeedsViewScrolledWindow(description=False, tags=True)
        self.filter_flap.set_content(self.sidebar_stack)
        self.filter_sw_bin = Adw.Bin()
        self.filter_sw_bin.set_child(self.filter_sw)
        self.filter_sw_bin.get_style_context().add_class('background')
        self.filter_flap.set_flap(self.filter_sw_bin)

        self.searchbar = GFeedsSearchbar()
        self.connection_bar = GFeedsConnectionBar()
        self.webview = GFeedsWebView()

        self.left_headerbar = LeftHeaderbar(self.searchbar, self.leaflet)
        self.right_headerbar = RightHeaderbar(
            self.webview, self.leaflet, self.on_back_btn_clicked
        )

        for w in (
                self.left_headerbar, self.searchbar, self.connection_bar,
                self.filter_flap
        ):
            self.left_box.append(w)
        for w in (self.right_headerbar, self.webview):
            self.right_box.append(w)

        self.sidebar.listview_sw.connect_activate(
            self.on_sidebar_row_activated
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

        self.feedman.connect(
            'feedmanager_refresh_end', self.on_refresh_end
        )

        self.on_leaflet_folded()

    @Gtk.Template.Callback()
    def on_leaflet_folded(self, *args):
        if self.leaflet.get_folded():
            self.right_headerbar.back_btn.set_visible(True)
        else:
            self.right_headerbar.back_btn.set_visible(False)

    def on_back_btn_clicked(self, *args):
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

    def on_sidebar_row_activated(self, feed_item: FeedItem):
        if not feed_item:
            return
        feed_item.read = True
        if (
                self.confman.conf['open_youtube_externally'] and
                reduce(or_, [
                    f'://{pfx}' in feed_item.link
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
