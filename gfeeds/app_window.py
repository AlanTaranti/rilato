from gfeeds.main_leaflet import MainLeaflet
from gfeeds.confManager import ConfManager
from gfeeds.feeds_manager import FeedsManager
from gfeeds.base_app import BaseWindow, AppShortcut
from datetime import datetime


class GFeedsAppWindow(BaseWindow):
    def __init__(self, application):
        self.confman = ConfManager()
        self.feedman = FeedsManager()
        self.app = application

        self.leaflet = MainLeaflet()

        super().__init__(
            app_name='Feeds',
            icon_name='org.gabmus.gfeeds',
            shortcuts=[
                AppShortcut(
                    'F10', lambda *args:
                        self.leaflet.left_headerbar.menu_btn.popup()
                ),
                AppShortcut(
                    '<Control>r', self.feedman.refresh
                ),
                AppShortcut(
                    '<Control>f', lambda *args:
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
                )
            ]
        )

        self.append(self.leaflet)

        self.confman.connect(
            'dark_mode_changed',
            lambda *args: self.set_dark_mode(self.confman.conf['dark_mode'])
        )
        self.set_dark_mode(self.confman.conf['dark_mode'])

    def present(self):
        super().present_with_time(int(datetime.now().timestamp()))
        self.set_default_size(
            self.confman.conf['windowsize']['width'],
            self.confman.conf['windowsize']['height']
        )

    def emit_destroy(self, *_):
        self.emit('destroy')

    def on_destroy(self, *_):
        self.leaflet.sidebar.listview_sw.shutdown_thread_pool()
        self.confman.conf['windowsize'] = {
            'width': self.get_width(),
            'height': self.get_height()
        }
        # cleanup old read items
        feeds_items_ids = [
            fi.identifier for fi in self.feedman.article_store.list_store
        ]
        to_rm = []
        for ri in self.confman.conf['read_items']:
            if ri not in feeds_items_ids:
                to_rm.append(ri)
        for ri in to_rm:
            self.confman.conf['read_items'].remove(ri)
        self.confman.save_conf()
        self.confman.save_article_thumb_cache()
