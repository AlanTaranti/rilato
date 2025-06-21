from gi.repository import Gio
from rilato.main_leaflet import MainLeaflet
from rilato.confManager import ConfManager
from rilato.feeds_manager import FeedsManager
from rilato.base_app import BaseWindow, AppShortcut
from datetime import datetime


class RilatoAppWindow(BaseWindow):
    def __init__(self, application):
        self.confman = ConfManager()
        self.feedman = FeedsManager()
        self.app = application

        self.leaflet = MainLeaflet()

        super().__init__(
            app_name='Feeds',
            icon_name='org.gabmus.rilato',
            shortcuts=[
                AppShortcut(
                    'F10', lambda *_:
                        self.leaflet.left_headerbar.menu_btn.popup()
                ),
                AppShortcut(
                    '<Control>r', self.feedman.refresh
                ),
                AppShortcut(
                    '<Control>f', lambda *_:
                        self.leaflet.left_headerbar.search_btn.set_active(
                            not
                            self.leaflet.left_headerbar.search_btn.get_active()
                        )
                ),
                AppShortcut(
                    '<Control>j', self.leaflet.sidebar.select_next_article
                ),
                AppShortcut(
                    '<Control>k', self.leaflet.sidebar.select_prev_article
                ),
                AppShortcut(
                    '<Control>plus', self.leaflet.webview.key_zoom_in
                ),
                AppShortcut(
                    '<Control>minus', self.leaflet.webview.key_zoom_out
                ),
                AppShortcut(
                    '<Control>equal', self.leaflet.webview.key_zoom_reset
                ),
                AppShortcut(
                    '<Control>t', lambda *_:
                        self.leaflet.filter_flap.set_reveal_flap(
                            not self.leaflet.filter_flap.get_reveal_flap()
                        )
                )
            ]
        )

        self.append(self.leaflet)

        self.confman.conf.gs.bind(
            'dark-mode', self, 'dark_mode', Gio.SettingsBindFlags.DEFAULT
        )
        self.dark_mode = self.confman.nconf.dark_mode

    def present(self):
        super().present_with_time(int(datetime.now().timestamp()))
        self.set_default_size(
            self.confman.nconf.window_width,
            self.confman.nconf.window_height
        )

    def emit_destroy(self, *_):
        self.emit('destroy')

    def on_destroy(self, *_):
        self.leaflet.sidebar.listview_sw.shutdown_thread_pool()
        self.confman.nconf.window_width = self.get_width()
        self.confman.nconf.window_height = self.get_height()
        self.feedman.cleanup_read_items()
        self.confman.save_article_thumb_cache()
