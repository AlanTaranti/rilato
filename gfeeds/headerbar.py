from gettext import gettext as _
from gi.repository import Gtk, Gdk, Adw, GObject
from gfeeds.confManager import ConfManager
from gfeeds.feeds_manager import FeedsManager
from gfeeds.feeds_view import FeedsViewPopover
from gfeeds.view_mode_menu import GFeedsViewModeMenu


class AddFeedPopover(Gtk.Popover):
    def __init__(self, relative_to, **kwargs):
        super().__init__(**kwargs)
        self.confman = ConfManager()
        self.feedman = FeedsManager()

        self.builder = Gtk.Builder.new_from_resource(
            '/org/gabmus/gfeeds/ui/add_feed_box.ui'
        )
        self.set_autohide(True)
        relative_to.set_popover(self)
        self.container_box = self.builder.get_object('container_box')
        self.confirm_btn = self.builder.get_object('confirm_btn')
        self.confirm_btn.connect(
            'clicked',
            self.on_confirm_btn_clicked
        )
        self.url_entry = self.builder.get_object('url_entry')
        self.url_entry.connect('activate', self.on_url_entry_activate)
        self.already_subscribed_revealer = self.builder.get_object(
            'already_subscribed_revealer'
        )
        self.url_entry.connect(
            'changed',
            lambda *args:
            self.already_subscribed_revealer.set_reveal_child(False)
        )
        self.set_child(self.container_box)

    def on_url_entry_activate(self, *args):
        if self.confirm_btn.get_sensitive():
            self.on_confirm_btn_clicked(self.confirm_btn)

    def on_confirm_btn_clicked(self, btn):
        res = self.feedman.add_feed(self.url_entry.get_text(), True)
        if res:
            self.popdown()
            self.already_subscribed_revealer.set_reveal_child(False)
        else:
            self.already_subscribed_revealer.set_reveal_child(True)


class GFeedsHeaderbarRight(Gtk.WindowHandle):
    def __init__(self, webview, leaflet, back_btn_func):
        super().__init__(vexpand=False, hexpand=True)
        self.builder = Gtk.Builder.new_from_resource(
            '/org/gabmus/gfeeds/ui/headerbar.ui'
        )
        self.confman = ConfManager()
        self.webview = webview
        self.leaflet = leaflet
        self.back_btn_func = back_btn_func
        self.webview.connect('gfeeds_webview_load_start', self.on_load_start)
        self.webview.connect('gfeeds_webview_load_end', self.on_load_end)
        self.right_headerbar = self.builder.get_object(
            'right_headerbar'
        )
        self.set_child(self.right_headerbar)
        self.view_mode_menu_btn = self.builder.get_object(
            'view_mode_menu_btn'
        )
        self.view_mode_menu_btn_icon = self.builder.get_object(
            'view_mode_menu_btn_icon'
        )
        self.set_view_mode_icon(self.confman.conf['default_view'])
        self.view_mode_menu = GFeedsViewModeMenu(self.view_mode_menu_btn)
        self.open_externally_btn = self.builder.get_object(
            'open_externally_btn'
        )
        self.open_externally_btn.connect(
            'clicked', self.webview.open_externally
        )
        self.share_btn = self.builder.get_object('share_btn')
        self.share_btn.connect('clicked', self.copy_article_uri)

        self.title_squeezer = self.builder.get_object(
            'right_headerbar_squeezer'
        )
        self.right_title_container = self.builder.get_object(
            'right_headerbar_title_container'
        )
        self.title_label = self.builder.get_object('title_label')

        self.leaflet.connect('notify::folded', self.set_headerbar_controls)

        self.back_button = self.builder.get_object('back_btn')
        self.back_button.connect('clicked', lambda *args: self.back_btn_func())

    def set_view_mode_icon(self, mode):
        self.view_mode_menu_btn_icon.set_from_icon_name(
            {
                'webview': 'globe-alt-symbolic',
                'reader': 'ephy-reader-mode-symbolic',
                'rsscont': 'application-rss+xml-symbolic'
            }[mode]
        )

    def on_view_mode_change(self, target):
        self.view_mode_menu.popdown()
        if target == 'webview':
            self.webview.set_enable_reader_mode(False)
        elif target == 'reader':
            self.webview.set_enable_reader_mode(True)
        elif target == 'rsscont':
            self.webview.set_enable_rss_content(True)
        self.set_view_mode_icon(target)

    def set_article_title(self, title):
        self.title_label.set_text(title)

    def on_load_start(self, *args):
        self.view_mode_menu_btn.set_sensitive(False)

    def on_load_end(self, *args):
        self.view_mode_menu_btn.set_sensitive(True)

    def set_headerbar_controls(self, *args):
        if self.leaflet.get_folded():
            self.right_headerbar.set_show_title_buttons(True)
        else:
            self.right_headerbar.set_show_title_buttons(
                not self.confman.wm_decoration_on_left
            )

    def copy_article_uri(self, *args):
        Gdk.Display.get_default().get_clipboard().set(self.webview.uri)
        self.webview.show_notif()


class GFeedsHeaderbarLeft(Gtk.WindowHandle):
    __gsignals__ = {
        'squeeze': (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (bool,)
        )
    }

    def __init__(self, searchbar, leaflet):
        super().__init__(vexpand=False, hexpand=True)
        self.builder = Gtk.Builder.new_from_resource(
            '/org/gabmus/gfeeds/ui/headerbar.ui'
        )
        self.confman = ConfManager()
        self.feedman = FeedsManager()
        self.searchbar = searchbar
        self.leaflet = leaflet
        self.left_headerbar = self.builder.get_object(
            'left_headerbar'
        )
        self.set_child(self.left_headerbar)
        self.set_headerbar_controls()
        self.menu_btn = self.builder.get_object(
            'menu_btn'
        )

        self.search_btn = self.builder.get_object('search_btn')
        self.search_btn.connect('toggled', self.on_search_btn_toggled)
        self.filter_btn = self.builder.get_object(
            'filter_btn'
        )
        self.filter_popover = FeedsViewPopover(self.filter_btn)
        self.filter_btn.set_popover(self.filter_popover)
        # this activates the "All" feed filter. while this works it's kinda
        # hacky and needs a proper function
        self.feedman.connect(
            'feedmanager_refresh_start',
            lambda caller, msg:
            self.filter_popover.scrolled_win.listbox.row_all_activate(
                skip=(msg == 'startup')
            )
        )

        self.add_btn = self.builder.get_object(
            'add_btn'
        )
        self.add_btn.set_tooltip_text(_('Add new feed'))
        self.add_popover = AddFeedPopover(self.add_btn)
        self.add_btn.set_popover(self.add_popover)

        self.refresh_btn = self.builder.get_object('refresh_btn')
        self.refresh_btn.connect('clicked', self.feedman.refresh)

        self.squeezer = Adw.Squeezer(orientation=Gtk.Orientation.HORIZONTAL)
        self.squeezer.set_homogeneous(False)
        self.squeezer.set_interpolate_size(False)
        self.squeezer.set_hexpand(False)
        self.nobox = Gtk.Label()
        self.nobox.set_size_request(1, -1)
        self.stack_switcher = Adw.ViewSwitcher(
            policy=Adw.ViewSwitcherPolicy.WIDE,
            margin_start=12, margin_end=12
        )
        self.squeezer.add(self.stack_switcher)
        self.squeezer.add(self.nobox)
        self.squeezer.connect('notify::visible-child', self.on_squeeze)
        self.left_headerbar.set_title_widget(self.squeezer)

        self.feedman.connect(
            'feedmanager_refresh_start',
            self.on_new_feed_add_start
        )
        self.feedman.connect(
            'feedmanager_refresh_end',
            self.on_new_feed_add_end
        )
        self.on_new_feed_add_start()

        self.leaflet.connect('notify::folded', self.set_headerbar_controls)

    def on_squeeze(self, *args):
        self.emit(
            'squeeze',
            self.squeezer.get_visible_child() == self.nobox
        )

    def on_search_btn_toggled(self, togglebtn):
        self.searchbar.set_search_mode(togglebtn.get_active())

    def on_new_feed_add_start(self, *args):
        self.refresh_btn.set_sensitive(False)
        self.add_popover.confirm_btn.set_sensitive(False)

    def on_new_feed_add_end(self, *args):
        self.refresh_btn.set_sensitive(True)
        self.add_popover.confirm_btn.set_sensitive(True)
        self.add_popover.url_entry.set_text('')

    def set_headerbar_controls(self, *args):
        if self.leaflet.get_folded():
            self.left_headerbar.set_show_title_buttons(True)
        else:
            self.left_headerbar.set_show_title_buttons(
                self.confman.wm_decoration_on_left
            )
