from gettext import gettext as _
from gi.repository import Gtk
from gfeeds.confManager import ConfManager
from gfeeds.feeds_manager import FeedsManager
from gfeeds.view_mode_menu import GFeedsViewModeMenu
from gfeeds.scrolled_message_dialog import ScrolledMessageDialog
from xml.sax.saxutils import escape


VIEW_MODE_ICONS = {
    'webview': 'globe-alt-symbolic',
    'reader': 'ephy-reader-mode-symbolic',
    'rsscont': 'application-rss+xml-symbolic'
}


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
        self.right_headerbar = self.builder.get_object(
            'right_headerbar'
        )
        self.set_child(self.right_headerbar)
        self.view_mode_menu_btn = self.builder.get_object(
            'view_mode_menu_btn'
        )
        self.view_mode_menu = GFeedsViewModeMenu(self.view_mode_menu_btn)
        self.set_view_mode_icon(self.confman.conf['default_view'])

        self.extra_menu_btn = self.builder.get_object('webview_extra_menu_btn')
        self.zoom_in_btn = self.builder.get_object('zoom_in_btn')
        self.zoom_out_btn = self.builder.get_object('zoom_out_btn')
        self.zoom_reset_btn = self.builder.get_object('zoom_reset_btn')
        self.zoom_in_btn.connect('clicked', self.webview.key_zoom_in)
        self.zoom_out_btn.connect('clicked', self.webview.key_zoom_out)
        self.zoom_reset_btn.connect('clicked', self.webview.key_zoom_reset)

        self.on_zoom_changed(None, self.confman.conf['webview_zoom'])
        self.webview.connect('zoom_changed', self.on_zoom_changed)

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

    def on_zoom_changed(self, caller, n_zoom: float):
        self.zoom_reset_btn.set_label(f'{round(n_zoom*100)}%')

    def set_view_mode_icon(self, mode):
        self.view_mode_menu_btn.set_icon_name(
            VIEW_MODE_ICONS[mode]
        )

    def on_view_mode_change(self, target):
        self.view_mode_menu.popdown()
        self.set_view_mode_icon(target)

    def set_article_title(self, title):
        self.title_label.set_text(title)

    def on_load_start(self, *args):
        self.view_mode_menu_btn.set_sensitive(True)

    def set_headerbar_controls(self, *args):
        if self.leaflet.get_folded():
            self.right_headerbar.set_show_title_buttons(True)
        else:
            self.right_headerbar.set_show_title_buttons(
                not self.confman.wm_decoration_on_left
            )


class GFeedsHeaderbarLeft(Gtk.WindowHandle):
    def __init__(self, searchbar, leaflet):
        super().__init__(vexpand=False, hexpand=True)
        # self.get_style_context().add_class('navigation-sidebar')
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
        self.filter_btn = self.builder.get_object('filter_btn')

        self.add_btn = self.builder.get_object(
            'add_btn'
        )
        self.add_btn.set_tooltip_text(_('Add new feed'))
        self.add_popover = AddFeedPopover(self.add_btn)
        self.add_btn.set_popover(self.add_popover)

        self.refresh_btn = self.builder.get_object('refresh_btn')
        self.refresh_btn.connect('clicked', self.feedman.refresh)

        self.errors_btn = self.builder.get_object('errors_btn')
        self.errors_btn.connect('clicked', self.show_errors_dialog)

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

    def show_errors_dialog(self, *args):
        dialog = ScrolledMessageDialog(
            transient_for=self.get_root(),
            modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=_(
                'There were problems with some feeds.\n'
                'Do you want to remove them?'
            )
        )
        dialog.format_secondary_markup(
            escape('\n'.join(self.feedman.errors))
        )

        def on_response(_dialog, res):
            _dialog.close()
            if (res == Gtk.ResponseType.YES):
                for pf in self.feedman.problematic_feeds:
                    if pf in self.confman.conf['feeds'].keys():
                        self.confman.conf['feeds'].pop(pf)
                        self.confman.save_conf()
                self.errors_btn.set_visible(False)
            else:
                self.errors_btn.set_visible(True)
            dialog.close()

        dialog.connect('response', on_response)
        dialog.present()

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
