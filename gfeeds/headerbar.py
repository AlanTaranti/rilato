from gettext import gettext as _
from typing import Dict, Optional
from gi.repository import Adw, GObject, Gtk
from gfeeds.confManager import ConfManager
from gfeeds.feeds_manager import FeedsManager
from xml.sax.saxutils import escape
from gfeeds.scrolled_dialog import ScrolledDialogResponse, ScrolledDialog
from gfeeds.webview import GFeedsWebView


VIEW_MODE_ICONS = {
    'webview': 'globe-alt-symbolic',
    'reader': 'ephy-reader-mode-symbolic',
    'feedcont': 'application-rss+xml-symbolic'
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
    def on_url_entry_changed(self, *__):
        self.already_subscribed_revealer.set_reveal_child(False)

    @Gtk.Template.Callback()
    def on_url_entry_activate(self, *__):
        if self.confirm_btn.get_sensitive():
            self.on_confirm_btn_clicked(self.confirm_btn)

    @Gtk.Template.Callback()
    def on_confirm_btn_clicked(self, __):
        url = self.url_entry.get_text().strip()
        if not url:
            return
        feed_is_new = self.feedman.add_feed(url, True)
        if feed_is_new:
            self.popdown()
            self.already_subscribed_revealer.set_reveal_child(False)
        else:
            self.already_subscribed_revealer.set_reveal_child(True)


@Gtk.Template(resource_path='/org/gabmus/gfeeds/ui/right_headerbar.ui')
class RightHeaderbar(Gtk.WindowHandle):
    __gtype_name__ = 'RightHeaderbar'
    __gsignals__ = {
        'go_back': (
            GObject.SignalFlags.RUN_LAST,
            None,
            (str,)
        )
    }
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

    def __init__(self, webview: Optional[GFeedsWebView] = None):
        super().__init__()
        self.confman = ConfManager()
        self.webview = webview
        self.set_view_mode_icon(self.confman.conf['default_view'])
        self.on_zoom_changed(None, self.confman.conf['webview_zoom'])

    @GObject.Property(type=GFeedsWebView, default=None, nick='webview')
    def webview(self) -> GFeedsWebView:  # type: ignore
        return self.__webview

    @webview.setter
    def webview(self, wv: GFeedsWebView):
        self.__webview = wv
        if wv is None:
            return
        self.__webview.connect('gfeeds_webview_load_start', self.on_load_start)
        self.__webview.connect('zoom_changed', self.on_zoom_changed)

    @Gtk.Template.Callback()
    def on_zoom_in_btn_clicked(self, *__):
        if self.webview is None:
            return
        self.webview.key_zoom_in()

    @Gtk.Template.Callback()
    def on_zoom_out_btn_clicked(self, *__):
        if self.webview is None:
            return
        self.webview.key_zoom_out()

    @Gtk.Template.Callback()
    def on_zoom_reset_btn_clicked(self, *__):
        if self.webview is None:
            return
        self.webview.key_zoom_reset()

    @Gtk.Template.Callback()
    def on_back_btn_clicked(self, *__):
        self.emit('go_back', '')

    def on_zoom_changed(self, __, n_zoom: float):
        self.zoom_reset_btn.set_label(f'{round(n_zoom*100)}%')

    def set_view_mode_icon(self, mode):
        self.view_mode_menu_btn.set_icon_name(
            VIEW_MODE_ICONS[mode]
        )

    def on_view_mode_change(self, target):
        self.set_view_mode_icon(target)

    def set_article_title(self, title):
        self.title_label.set_text(title)

    def on_load_start(self, *_):
        self.view_mode_menu_btn.set_sensitive(True)


@Gtk.Template(resource_path='/org/gabmus/gfeeds/ui/left_headerbar.ui')
class LeftHeaderbar(Gtk.WindowHandle):
    __gtype_name__ = 'LeftHeaderbar'
    left_headerbar = Gtk.Template.Child()
    menu_btn = Gtk.Template.Child()
    filter_btn = Gtk.Template.Child()
    add_btn = Gtk.Template.Child()
    refresh_btn = Gtk.Template.Child()
    search_btn = Gtk.Template.Child()
    errors_btn = Gtk.Template.Child()

    def __init__(self, searchbar: Optional[Gtk.SearchBar] = None):
        super().__init__()
        self.confman = ConfManager()
        self.feedman = FeedsManager()
        self.searchbar = searchbar

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

    @GObject.Property(
        type=Gtk.SearchBar, default=None, nick='searchbar'
    )
    def searchbar(self) -> Gtk.SearchBar:  # type: ignore
        return self.__searchbar

    @searchbar.setter
    def searchbar(self, sb: Gtk.SearchBar):
        self.__searchbar = sb

    @Gtk.Template.Callback()
    def on_refresh_btn_clicked(self, *__):
        self.feedman.refresh()

    @Gtk.Template.Callback()
    def show_errors_dialog(self, *__):

        def on_remove(d: ScrolledDialog, _):
            d.close()
            feeds: Dict[str, dict] = self.confman.conf['feeds']
            for pf in self.feedman.problematic_feeds:
                if pf in feeds.keys():
                    feeds.pop(pf)
            self.confman.conf['feeds'] = feeds
            self.errors_btn.set_visible(False)

        def on_keep(d: ScrolledDialog, _):
            d.close()
            self.errors_btn.set_visible(True)

        dialog = ScrolledDialog(
            self.get_root(),  # type: ignore
            _(
                'There were problems with some feeds.'
                ' Do you want to remove them?'
            ),
            escape('\n'.join(self.feedman.errors)),
            [
                ScrolledDialogResponse('keep', _('_Keep'), on_keep),
                ScrolledDialogResponse(
                    'remove', _('_Remove'), on_remove,
                    Adw.ResponseAppearance.DESTRUCTIVE
                )
            ]
        )
        dialog.present()

    @Gtk.Template.Callback()
    def on_search_btn_toggled(self, togglebtn):
        if self.searchbar is None:
            return
        self.searchbar.set_search_mode(togglebtn.get_active())

    def on_new_feed_add_start(self, *_):
        self.refresh_btn.set_sensitive(False)
        self.add_popover.confirm_btn.set_sensitive(False)

    def on_new_feed_add_end(self, *_):
        self.refresh_btn.set_sensitive(True)
        self.add_popover.confirm_btn.set_sensitive(True)
        self.add_popover.url_entry.set_text('')
