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


@Gtk.Template(resource_path='/org/gabmus/gfeeds/ui/add_feed_popover.ui')
class AddFeedPopover(Gtk.Popover):
    __gtype_name__ = 'AddFeedPopover'
    confirm_btn = Gtk.Template.Child()
    url_entry = Gtk.Template.Child()
    already_subscribed_revealer = Gtk.Template.Child()

    def __init__(self, relative_to):
        super().__init__()
        self.confman = ConfManager()
        self.feedman = FeedsManager()

        relative_to.set_popover(self)

    @Gtk.Template.Callback()
    def on_url_entry_changed(self, *args):
        self.already_subscribed_revealer.set_reveal_child(False)

    @Gtk.Template.Callback()
    def on_url_entry_activate(self, *args):
        if self.confirm_btn.get_sensitive():
            self.on_confirm_btn_clicked(self.confirm_btn)

    @Gtk.Template.Callback()
    def on_confirm_btn_clicked(self, btn):
        url = self.url_entry.get_text().strip()
        if not url:
            return
        res = self.feedman.add_feed(url, True)
        if res:
            self.popdown()
            self.already_subscribed_revealer.set_reveal_child(False)
        else:
            self.already_subscribed_revealer.set_reveal_child(True)


@Gtk.Template(resource_path='/org/gabmus/gfeeds/ui/right_headerbar.ui')
class GFeedsHeaderbarRight(Gtk.WindowHandle):
    __gtype_name__ = 'RightHeaderbar'
    right_headerbar = Gtk.Template.Child()
    view_mode_menu_btn = Gtk.Template.Child()
    extra_menu_btn = Gtk.Template.Child()
    zoom_in_btn = Gtk.Template.Child()
    zoom_out_btn = Gtk.Template.Child()
    zoom_reset_btn = Gtk.Template.Child()
    title_squeezer = Gtk.Template.Child()
    right_title_container = Gtk.Template.Child()
    title_label = Gtk.Template.Child()
    back_btn = Gtk.Template.Child()

    def __init__(self, webview, leaflet, back_btn_func):
        super().__init__()
        self.confman = ConfManager()
        self.webview = webview
        self.leaflet = leaflet
        self.back_btn_func = back_btn_func
        self.webview.connect('gfeeds_webview_load_start', self.on_load_start)
        self.view_mode_menu = GFeedsViewModeMenu(self.view_mode_menu_btn)
        self.set_view_mode_icon(self.confman.conf['default_view'])

        self.on_zoom_changed(None, self.confman.conf['webview_zoom'])
        self.webview.connect('zoom_changed', self.on_zoom_changed)

        self.leaflet.connect('notify::folded', self.set_headerbar_controls)

    @Gtk.Template.Callback()
    def on_zoom_in_btn_clicked(self, *args):
        self.webview.key_zoom_in()

    @Gtk.Template.Callback()
    def on_zoom_out_btn_clicked(self, *args):
        self.webview.key_zoom_out()

    @Gtk.Template.Callback()
    def on_zoom_reset_btn_clicked(self, *args):
        self.webview.key_zoom_reset()

    @Gtk.Template.Callback()
    def on_back_btn_clicked(self, *args):
        self.back_btn_func()

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


@Gtk.Template(resource_path='/org/gabmus/gfeeds/ui/left_headerbar.ui')
class GFeedsHeaderbarLeft(Gtk.WindowHandle):
    __gtype_name__ = 'LeftHeaderbar'
    left_headerbar = Gtk.Template.Child()
    menu_btn = Gtk.Template.Child()
    filter_btn = Gtk.Template.Child()
    add_btn = Gtk.Template.Child()
    refresh_btn = Gtk.Template.Child()
    errors_btn = Gtk.Template.Child()

    def __init__(self, searchbar, leaflet):
        super().__init__()
        self.confman = ConfManager()
        self.feedman = FeedsManager()
        self.searchbar = searchbar
        self.leaflet = leaflet
        self.set_headerbar_controls()

        self.add_popover = AddFeedPopover(self.add_btn)
        self.add_btn.set_popover(self.add_popover)

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

    @Gtk.Template.Callback()
    def on_refresh_btn_clicked(self, *args):
        self.feedman.refresh()

    @Gtk.Template.Callback()
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

    @Gtk.Template.Callback()
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
