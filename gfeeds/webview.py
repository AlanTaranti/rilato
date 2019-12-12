from subprocess import Popen
from time import sleep
from gettext import gettext as _
import threading
from feedparser import FeedParserDict
from gi.repository import Gtk, GLib, WebKit2, GObject
from gfeeds.build_reader_html import build_reader_html
from gfeeds.confManager import ConfManager
from gfeeds.download_manager import download_text
from gfeeds.revealer_loading_bar import RevealerLoadingBar


class GFeedsWebView(Gtk.Stack):
    __gsignals__ = {
        'gfeeds_webview_load_end': (
            GObject.SIGNAL_RUN_LAST,
            None,
            (str,)
        ),
        'gfeeds_webview_load_start': (
            GObject.SIGNAL_RUN_FIRST,
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
            '/org/gabmus/gfeeds/ui/webview_filler.glade'
        )
        self.webview_notif_builder = Gtk.Builder.new_from_resource(
            '/org/gabmus/gfeeds/ui/webview_with_notification.glade'
        )

        self.webkitview = WebKit2.WebView()
        self.loading_bar = RevealerLoadingBar()
        self.webview_notif_builder.get_object(
            'box1'
        ).pack_start(self.loading_bar, False, False, 0)
        self.webview_notif_builder.get_object(
            'box1'
        ).pack_end(self.webkitview, True, True, 0)
        self.overlay_container = self.webview_notif_builder.get_object(
            'overlay1'
        )
        self.notif_revealer = self.webview_notif_builder.get_object(
            'revealer'
        )
        self.webview_notif_builder.get_object(
            'notif_close_btn'
        ).connect('clicked', self.hide_notif)

        self.webkitview_settings = WebKit2.Settings()
        self.apply_webview_settings()
        self.confman.connect(
            'gfeeds_webview_settings_changed',
            self.apply_webview_settings
        )

        self.webkitview.connect('load-changed', self.on_load_changed)
        self.webkitview.connect("decide-policy", self.on_decide_policy)

        self.fillerview = self.filler_builder.get_object('webview_filler_box')

        self.webkitview.set_hexpand(True)
        self.fillerview.set_hexpand(True)
        self.webkitview.set_size_request(360, 500)
        self.fillerview.set_size_request(360, 500)

        self.add_titled(self.overlay_container, 'Web View', _('Web View'))
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

    def _wait_async(self, tts, callback):
        sleep(tts)
        callback()

    def show_notif(self, *args):
        self.notif_revealer.set_reveal_child(True)
        t = threading.Thread(
            group=None,
            target=self._wait_async,
            name=None,
            args=(5, lambda: GLib.idle_add(self.hide_notif))
        )
        t.start()

    def hide_notif(self, *args):
        self.notif_revealer.set_reveal_child(False)

    def set_enable_rss_content(self, togglebtn, state=None, feeditem=None):
        if state == None:
            state = togglebtn.get_active()
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
        if feeditem.is_saved:
            self.set_enable_reader_mode(None, True, False)
            return
        self.set_visible_child(self.overlay_container)
        self.feeditem = feeditem
        self.uri = feeditem.link
        content = feeditem.fp_item.get(
            'content', feeditem.fp_item.get('summary', None)
        )
        if not content:
            content = '<h1><i>'+_(
                'RSS content or summary not available for this article'
                )+'</i></h1>'
        elif not isinstance(content, str):
            if isinstance(content, list):
                content = content[0]
            if isinstance(content, (dict, FeedParserDict)):
                if 'value' in content.keys():
                    content = content['value']
        self.html = '<!-- GFEEDS RSS CONTENT --><article>{0}</article>'.format(
            content if '</' in content else content.replace('\n', '<br>')
        )
        self.set_enable_reader_mode(None, True, True)

    def _load_reader_async(self, callback=None, *args):
        self.html = download_text(self.uri)
        GLib.idle_add(
            self.set_enable_reader_mode, None, True
        )
        if callback:
            GLib.idle_add(callback)

    def load_feeditem(self, feeditem, trigger_on_load_start=True, *args, **kwargs):
        uri = feeditem.link
        if feeditem.is_saved:
            uri = (
                'file://' +
                self.confman.saved_cache_path + '/' +
                feeditem.fp_item['linkhash']
            )
        self.feeditem = feeditem
        self.uri = uri
        self.set_visible_child(self.overlay_container)
        if self.confman.conf['default_view'] == 'reader':
            t = threading.Thread(
                group=None,
                target=self._load_reader_async,
                name=None,
                # args = (uri,)
            )
            if trigger_on_load_start:
                self.on_load_start()
            t.start()
        elif self.confman.conf['default_view'] == 'rsscont':
            self.on_load_start()
            self.set_enable_rss_content(None, True, feeditem)
        else:
            self.webkitview.load_uri(uri) # , *args, **kwargs)
            if trigger_on_load_start:
                self.on_load_start()

    def open_externally(self, *args):
        if self.uri:
            Popen(f'xdg-open {self.uri}'.split(' '))

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
            # waits 5 seconds async then hides the loading bar
            t = threading.Thread(
                group=None,
                target=self._wait_async,
                name=None,
                args=(
                    3,
                    lambda: GLib.idle_add(
                        self.loading_bar.set_reveal_child, False
                    )
                )
            )
            t.start()
            self.new_page_loaded = False
            resource = webview.get_main_resource()
            resource.get_data(None, self._get_data_cb, None)

    def _set_enable_reader_mode_async_callback(self):
        self.webkitview.load_html(build_reader_html(
            self.html,
            self.confman.conf['dark_reader'],
            None
        ), self.uri)

    def _set_enable_reader_mode_async_callback_rss(self):
        self.webkitview.load_html(build_reader_html(
            self.html,
            self.confman.conf['dark_reader'],
            self.feeditem.fp_item
        ), self.uri)

    def set_enable_reader_mode(self, togglebtn, state=None, is_rss_content=False):
        if state == None:
            state = togglebtn.get_active()
        if state:
            if (
                    not self.html or (
                        not is_rss_content and
                        self.html[:36] == '<!-- GFEEDS RSS CONTENT --><article>'
                    )
            ):
                t = threading.Thread(
                    group=None,
                    target=self._load_reader_async,
                    name=None,
                    args=(
                        self._set_enable_reader_mode_async_callback,
                    )
                )
                # self.on_load_start()
                t.start()
            else:
                self._set_enable_reader_mode_async_callback_rss()
        else:
            self.webkitview.load_uri(self.uri)

    def _get_data_cb(self, resource, result, user_data=None):
        self.html = resource.get_data_finish(result)

    def on_decide_policy(self, webView, decision, decisionType):
        if not self.confman.conf['open_links_externally']:
            return False
        if (
                decisionType == WebKit2.PolicyDecisionType.NAVIGATION_ACTION and
                decision.get_navigation_action().get_mouse_button() != 0
        ):
            decision.ignore()
            uri = decision.get_navigation_action().get_request().get_uri()
            Popen(f'xdg-open {uri}'.split(' '))
            return True
        return False
