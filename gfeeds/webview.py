from gettext import gettext as _
import threading
from gi.repository import Gtk, GLib, WebKit2, GObject, Gio, Adw
from gfeeds.build_reader_html import build_reader_html
from gfeeds.confManager import ConfManager
from gfeeds.download_manager import download_text
from gfeeds.revealer_loading_bar import RevealerLoadingBar
from functools import reduce
from operator import or_
from subprocess import Popen


class GFeedsWebView(Gtk.Stack):
    __gsignals__ = {
        'gfeeds_webview_load_end': (
            GObject.SignalFlags.RUN_LAST,
            None,
            (str,)
        ),
        'gfeeds_webview_load_start': (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (str,)
        )
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.confman = ConfManager()
        self.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.set_hexpand(True)
        self.set_size_request(360, 500)

        self.filler_builder = Gtk.Builder.new_from_resource(
            '/org/gabmus/gfeeds/ui/webview_filler.ui'
        )
        self.webview_notif_builder = Gtk.Builder.new_from_resource(
            '/org/gabmus/gfeeds/ui/toast_webview.ui'
        )

        self.webkitview = WebKit2.WebView(
            hexpand=True, vexpand=True, width_request=360, height_request=500
        )
        self.loading_bar = RevealerLoadingBar()
        self.webview_notif_builder.get_object(
            'loading_bar_container'
        ).set_child(self.loading_bar)
        self.main_view = self.webview_notif_builder.get_object('container_box')
        self.toast_overlay = self.webview_notif_builder.get_object(
            'toast_overlay'
        )
        self.toast_overlay.set_child(self.webkitview)

        self.webkitview_settings = WebKit2.Settings()
        self.apply_webview_settings()
        self.confman.connect(
            'gfeeds_webview_settings_changed',
            self.apply_webview_settings
        )

        self.webkitview.connect('load-changed', self.on_load_changed)
        self.webkitview.connect('decide-policy', self.on_decide_policy)

        self.fillerview = self.filler_builder.get_object('webview_filler_box')

        self.add_titled(self.main_view, 'Web View', _('Web View'))
        self.add_titled(self.fillerview, 'Filler View', _('Filler View'))
        self.set_visible_child(self.fillerview)

        self.new_page_loaded = False
        self.uri = ''
        self.feeditem = None
        self.html = None

    def apply_webview_settings(self, *args):
        self.webkitview_settings.set_enable_javascript(
            self.confman.conf['enable_js']
        )
        self.webkitview_settings.set_enable_smooth_scrolling(True)
        self.webkitview_settings.set_enable_page_cache(True)
        self.webkitview_settings.set_enable_frame_flattening(True)
        self.webkitview_settings.set_enable_accelerated_2d_canvas(True)
        self.webkitview.set_settings(self.webkitview_settings)

    def key_zoom_in(self, *args):
        self.webkitview.set_zoom_level(
            self.webkitview.get_zoom_level()+0.15
        )

    def key_zoom_out(self, *args):
        self.webkitview.set_zoom_level(
            self.webkitview.get_zoom_level()-0.15
        )

    def key_zoom_reset(self, *args):
        self.webkitview.set_zoom_level(1.0)

    def show_notif(self, *args):
        toast = Adw.Toast(title=_('Link copied to clipboard!'))
        self.toast_overlay.add_toast(toast)

    def set_enable_rss_content(self, state=True, feeditem=None):
        if feeditem:
            self.feeditem = feeditem
        if state:
            self._load_rss_content(self.feeditem)
        else:
            self.new_page_loaded = True
            self.load_feeditem(
                self.feeditem,
                False
            )

    def _load_rss_content(self, feeditem):
        self.set_visible_child(self.main_view)
        self.feeditem = feeditem
        self.uri = feeditem.link
        content = feeditem.sd_item.get_content()
        if not content:
            content = '<h1><i>'+_(
                'RSS content or summary not available for this article'
                )+'</i></h1>'
        self.html = '<!-- GFEEDS RSS CONTENT --><article>{0}</article>'.format(
            content if '</' in content else content.replace('\n', '<br>')
        )
        self.set_enable_reader_mode(True, True)

    def _load_reader_async(self, callback=None, *args):
        self.html = download_text(self.uri)
        GLib.idle_add(
            self.set_enable_reader_mode, True
        )
        if callback:
            GLib.idle_add(callback)

    def load_feeditem(self, feeditem, trigger_on_load_start=True,
                      *args, **kwargs):
        self.webkitview.stop_loading()
        uri = feeditem.link
        self.feeditem = feeditem
        self.uri = uri
        self.set_visible_child(self.main_view)
        if self.confman.conf['default_view'] == 'reader':
            t = threading.Thread(
                group=None,
                target=self._load_reader_async,
                name=None,
                daemon=True
                # args = (uri,)
            )
            if trigger_on_load_start:
                self.on_load_start()
            t.start()
        elif self.confman.conf['default_view'] == 'rsscont':
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

    def on_load_changed(self, webview, event):
        if event != WebKit2.LoadEvent.FINISHED:
            self.loading_bar.set_reveal_child(True)
        if event == WebKit2.LoadEvent.STARTED:
            self.loading_bar.set_fraction(.25)
        elif event == WebKit2.LoadEvent.REDIRECTED:
            self.loading_bar.set_fraction(.50)
        elif event == WebKit2.LoadEvent.COMMITTED:
            self.emit('gfeeds_webview_load_end', '')
            self.loading_bar.set_fraction(.75)
        elif self.new_page_loaded and event == WebKit2.LoadEvent.FINISHED:
            self.loading_bar.set_fraction(1.0)
            # waits 1 seconds async then hides the loading bar
            GLib.timeout_add_seconds(
                1,
                self.loading_bar.set_reveal_child, False
            )
            self.new_page_loaded = False
            resource = webview.get_main_resource()
            resource.get_data(None, self._get_data_cb, None)

    def _set_enable_reader_mode_async_callback(self):
        self.webkitview.load_html(build_reader_html(
            self.html,
            self.confman.conf['dark_reader'],
            self.feeditem.sd_item
        ), self.uri)

    def set_enable_reader_mode(self, state=True, is_rss_content=False):
        if state:
            if (
                    not self.html or (
                        not is_rss_content and
                        (
                            self.html[:36] ==
                            '<!-- GFEEDS RSS CONTENT --><article>'
                        )
                    )
            ):
                t = threading.Thread(
                    group=None,
                    target=self._load_reader_async,
                    name=None,
                    args=(
                        self._set_enable_reader_mode_async_callback,
                    ),
                    daemon=True
                )
                t.start()
            else:
                self._set_enable_reader_mode_async_callback()
        else:
            self.webkitview.load_uri(self.uri)

    def _get_data_cb(self, resource, result, user_data=None):
        self.html = resource.get_data_finish(result)

    def on_decide_policy(self, webView, decision, decisionType):
        if not self.confman.conf['open_links_externally']:
            return False
        if (
                decisionType in
                (
                    WebKit2.PolicyDecisionType.NAVIGATION_ACTION,
                    WebKit2.PolicyDecisionType.NEW_WINDOW_ACTION
                ) and
                decision.get_navigation_action().get_mouse_button() != 0
        ):
            decision.ignore()
            uri = decision.get_navigation_action().get_request().get_uri()
            if (
                    self.confman.conf['open_youtube_externally'] and
                    reduce(or_, [
                        f'://{pfx}' in uri
                        for pfx in [
                            p + 'youtube.com'
                            for p in ('', 'www.', 'm.')
                        ]
                    ])
            ):
                cmd_parts = [
                    self.confman.conf['media_player'], f'"{uri}"'
                ]
                if self.confman.is_flatpak:
                    cmd_parts.insert(0, 'flatpak-spawn --host')
                cmd = ' '.join(cmd_parts)
                Popen(cmd, shell=True)
            else:
                Gio.AppInfo.launch_default_for_uri(uri)
            return True
        return False
