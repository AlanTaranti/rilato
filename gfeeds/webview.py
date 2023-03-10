from gettext import gettext as _
from threading import Thread
from gi.repository import Gtk, GLib, WebKit2, GObject, Gio, Adw
from gfeeds.util.build_reader_html import build_reader_html
from gfeeds.confManager import ConfManager
from gfeeds.util.download_manager import DownloadError, download_text
from functools import reduce
from operator import or_
from subprocess import Popen
from datetime import datetime
from typing import Optional
from gfeeds.feed_item import FeedItem
from gfeeds.util.paths import CACHE_PATH, IS_FLATPAK


@Gtk.Template(resource_path='/org/gabmus/gfeeds/ui/webview.ui')
class GFeedsWebView(Gtk.Stack):
    __gtype_name__ = 'GFeedsWebView'
    webkitview = Gtk.Template.Child()
    loading_bar_revealer = Gtk.Template.Child()
    loading_bar = Gtk.Template.Child()
    main_view = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    link_preview_revealer = Gtk.Template.Child()
    link_preview_label = Gtk.Template.Child()

    __gsignals__ = {
        'gfeeds_webview_load_start': (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (str,)
        ),
        'zoom_changed': (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (float,)
        )
    }

    def __init__(self):
        super().__init__()
        self.confman = ConfManager()

        self.webkitview_settings = WebKit2.Settings()
        self.apply_webview_settings()

        self.confman.connect(
            'gfeeds_webview_settings_changed',
            self.apply_webview_settings
        )

        self.confman.connect(
            'on_apply_adblock_changed',
            lambda *args: self.on_apply_adblock_changed(False)
        )
        self.confman.connect(
            'on_refresh_blocklist',
            lambda *args: self.on_apply_adblock_changed(True)
        )

        self.content_manager = self.webkitview.get_user_content_manager()
        self.user_content_filter_store = WebKit2.UserContentFilterStore.new(
            str(CACHE_PATH.joinpath(
                'webkit_user_content_filter_store'
            ))
        )
        if self.confman.nconf.enable_adblock:
            self.apply_adblock()

        self.webkitview.set_zoom_level(self.confman.nconf.webview_zoom)

        self.new_page_loaded = False
        self.uri = ''
        self.feeditem = None
        self.html = None

    @Gtk.Template.Callback()
    def on_mouse_target_changed(self, webkitview, hit_test_result, modifiers):
        if hit_test_result:
            if hit_test_result.context_is_link():
                self.link_preview_revealer.set_visible(True)
                self.link_preview_revealer.set_reveal_child(True)
                self.link_preview_label.set_text(
                    hit_test_result.get_link_uri()
                )
                return
        self.link_preview_revealer.set_visible(False)
        self.link_preview_revealer.set_reveal_child(False)

    def action_open_media_player(self):
        self.open_url_in_media_player(
            self.feeditem.link if self.feeditem else None
        )

    def on_apply_adblock_changed(self, refresh: bool):
        self.apply_adblock(
            refresh=refresh, remove=not self.confman.nconf.enable_adblock
        )

    def apply_adblock(self, refresh: bool = False, remove: bool = False):
        refresh = refresh or (
            datetime.fromtimestamp(
                self.confman.nconf.blocklist_last_update
            ) - datetime.now()
        ).days >= 10

        if refresh or remove:
            self.content_manager.remove_filter_by_id('blocklist')
        if remove:
            return

        def apply_filter(filter: WebKit2.UserContentFilter):
            self.content_manager.add_filter(filter)

        def save_blocklist_cb(caller, res, *args):
            try:
                filter = self.user_content_filter_store.save_finish(res)
                apply_filter(filter)
            except GLib.Error:
                print('Error saving blocklist')

        def download_blocklist_cb(blocklist: str):
            self.user_content_filter_store.save(
                'blocklist', GLib.Bytes.new(blocklist.encode()), None,
                save_blocklist_cb
            )

        def download_blocklist():
            res = download_text(
                'https://easylist-downloads.adblockplus.org/'
                'easylist_min_content_blocker.json'
            )
            now = datetime.now()
            print(f'Downloaded updated blocklist at {now}')
            self.confman.nconf.blocklist_last_update = now.timestamp()
            GLib.idle_add(download_blocklist_cb, res)

        def filter_load_cb(caller, res, *args):
            try:
                filter = self.user_content_filter_store.load_finish(res)
                apply_filter(filter)
                print('Loaded stored blocklist')
            except GLib.Error:
                print('blocklist store not found, downloading...')
                Thread(target=download_blocklist, daemon=True).start()

        if refresh:
            Thread(target=download_blocklist, daemon=True).start()
        else:
            self.user_content_filter_store.load(
                'blocklist', None, filter_load_cb, None
            )

    def change_view_mode(self, target):
        if target == 'webview':
            # if uri is empty force rss content
            if not self.uri:
                if not self.feeditem:
                    return
                return self.load_feeditem(self.feeditem, force_feedcont=True)
            self.webkitview.load_uri(self.uri)
        elif target == 'reader':
            Thread(
                target=self._load_reader_async,
                args=(self.load_reader,), daemon=True
            ).start()
        elif target == 'feedcont':
            self.set_enable_rss_content(True)

    def apply_webview_settings(self, *args):
        self.webkitview_settings.set_enable_javascript(
            self.confman.nconf.enable_js
        )
        self.webkitview_settings.set_enable_smooth_scrolling(True)
        self.webkitview_settings.set_enable_page_cache(True)
        self.webkitview_settings.set_enable_back_forward_navigation_gestures(
            True
        )
        self.webkitview_settings.set_enable_accelerated_2d_canvas(True)
        self.webkitview.set_settings(self.webkitview_settings)

    def key_zoom_in(self, *args):
        self.webkitview.set_zoom_level(
            self.webkitview.get_zoom_level()+0.10
        )
        self.on_zoom_changed()

    def key_zoom_out(self, *args):
        self.webkitview.set_zoom_level(
            self.webkitview.get_zoom_level()-0.10
        )
        self.on_zoom_changed()

    def key_zoom_reset(self, *args):
        self.webkitview.set_zoom_level(1.0)
        self.on_zoom_changed()

    def on_zoom_changed(self):
        zoom = self.webkitview.get_zoom_level()
        self.emit('zoom_changed', zoom)
        self.confman.nconf.webview_zoom = zoom

    def show_notif(self, *args):
        toast = Adw.Toast(title=_('Link copied to clipboard!'))
        self.toast_overlay.add_toast(toast)

    def set_enable_rss_content(self, state=True, feeditem=None):
        if feeditem:
            self.feeditem = feeditem
        if state:
            self.load_rss_content(self.feeditem)
        else:
            self.new_page_loaded = True
            self.load_feeditem(
                self.feeditem,
                False
            )

    def load_rss_content(self, feeditem):
        self.set_visible_child(self.main_view)
        self.feeditem = feeditem
        self.uri = feeditem.link
        content = feeditem.content
        if not content:
            content = '<h1><i>'+_(
                'Feed content not available for this article'
                )+'</i></h1>'
        self.html = '<!-- GFEEDS RSS CONTENT --><article>{0}</article>'.format(
            content if '</' in content else content.replace('\n', '<br>')
        )
        self.load_reader()

    def _load_reader_async(self, callback=None, *args):
        # if uri is empty force rss content
        if not self.uri:
            if not self.feeditem:
                return
            return self.load_feeditem(self.feeditem, force_feedcont=True)
        try:
            self.html = download_text(self.uri)
        except DownloadError as err:
            self.html = (
                f'<h1>{_("Error downloading content.")}</h1>'
                f'<h3>{_("Error code:")} {err.download_error_code}</h3>'
            )
        if callback:
            GLib.idle_add(callback)

    def load_feeditem(
            self, feeditem: FeedItem,
            trigger_on_load_start: Optional[bool] = True,
            force_feedcont: Optional[bool] = False
    ):
        self.webkitview.stop_loading()
        uri = feeditem.link
        self.feeditem = feeditem
        self.uri = uri
        self.set_visible_child(self.main_view)
        target = self.confman.nconf.default_view
        # if uri is empty, fallback to rss content
        if not uri or force_feedcont:
            target = 'feedcont'
        if target == 'reader':
            Thread(
                target=self._load_reader_async,
                args=(self.load_reader,),
                daemon=True
            ).start()
            if trigger_on_load_start:
                self.on_load_start()
        elif target == 'feedcont':
            self.on_load_start()
            self.set_enable_rss_content(True, feeditem)
        else:
            self.webkitview.load_uri(uri)
            if trigger_on_load_start:
                self.on_load_start()

    def open_externally(self, *args):
        if self.uri:
            Gio.AppInfo.launch_default_for_uri(
                self.uri
            )

    def on_load_start(self, *args):
        self.new_page_loaded = True
        self.emit('gfeeds_webview_load_start', '')

    @Gtk.Template.Callback()
    def on_load_changed(self, webview, event):
        if event != WebKit2.LoadEvent.FINISHED:
            self.loading_bar_revealer.set_reveal_child(True)
        if event == WebKit2.LoadEvent.STARTED:
            self.loading_bar.set_fraction(.25)
        elif event == WebKit2.LoadEvent.REDIRECTED:
            self.loading_bar.set_fraction(.50)
        elif event == WebKit2.LoadEvent.COMMITTED:
            self.loading_bar.set_fraction(.75)
        elif event == WebKit2.LoadEvent.FINISHED:
            self.loading_bar.set_fraction(1.0)
            # waits 1 seconds async then hides the loading bar
            GLib.timeout_add_seconds(
                1,
                self.loading_bar_revealer.set_reveal_child, False
            )
            self.new_page_loaded = False
            resource = webview.get_main_resource()
            if resource:
                resource.get_data(None, self._get_data_cb, None)

    def load_reader(self):
        if not self.feeditem:
            return
        dark = False
        if self.confman.nconf.reader_theme == 'auto':
            dark = Adw.StyleManager.get_default().get_dark()
        else:
            dark = self.confman.nconf.reader_theme == 'dark'
        self.webkitview.load_html(build_reader_html(
            self.html,
            self.feeditem,
            dark,
        ), self.uri)

    def _get_data_cb(self, resource, result, __=None):
        self.html = resource.get_data_finish(result)

    def open_url_in_media_player(self, url: Optional[str]):
        if not url:
            return
        cmd_parts = [
            self.confman.nconf.media_player, f"'{url}'"
        ]
        if IS_FLATPAK:
            cmd_parts.insert(0, 'flatpak-spawn --host')
        cmd = ' '.join(cmd_parts)
        Popen(cmd, shell=True)

    @Gtk.Template.Callback()
    def on_decide_policy(self, webView, decision, decisionType):
        if (
                decisionType in
                (
                    WebKit2.PolicyDecisionType.NAVIGATION_ACTION,
                    WebKit2.PolicyDecisionType.NEW_WINDOW_ACTION
                ) and
                decision.get_navigation_action().get_mouse_button() != 0
        ):
            uri = decision.get_navigation_action().get_request().get_uri()
            if (
                    self.confman.nconf.open_youtube_externally and
                    reduce(or_, [
                        f'://{pfx}' in uri
                        for pfx in [
                            p + 'youtube.com'
                            for p in ('', 'www.', 'm.')
                        ]
                    ])
            ):
                decision.ignore()
                self.open_url_in_media_player(uri)
            else:
                if not self.confman.nconf.open_links_externally:
                    return False
                decision.ignore()
                Gio.AppInfo.launch_default_for_uri(uri)
            return True
        return False
