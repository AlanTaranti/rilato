from pathlib import Path
from os.path import isfile
from os import environ as Env
import json
from datetime import timedelta
from gi.repository import GObject, Gio
from threading import Thread
from gfeeds.util.singleton import Singleton


class ConfManagerSignaler(GObject.Object):

    __gsignals__ = {
        'gfeeds_new_first_changed': (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (str,)
        ),
        'gfeeds_repopulation_required': (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (str,)
        ),
        'gfeeds_webview_settings_changed': (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (str,)
        ),
        'gfeeds_show_read_changed': (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (str,)
        ),
        'gfeeds_full_article_title_changed': (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (str,)
        ),
        'gfeeds_show_empty_feeds_changed': (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (str,)
        ),
        # Signals down here don't have to do with the config
        'gfeeds_filter_changed': (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (GObject.TYPE_PYOBJECT,)
        ),
        'gfeeds_full_feed_name_changed': (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (str,)
        ),
        'gfeeds_tags_append': (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (str,)
        ),
        'gfeeds_tags_pop': (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (str,)
        ),
        'dark_mode_changed': (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (str,)
        ),
        'show_thumbnails_changed': (
            GObject.SignalFlags.RUN_LAST,
            None,
            (str,)
        ),
        'on_apply_adblock_changed': (
            GObject.SignalFlags.RUN_LAST,
            None,
            (str,)
        ),
        'on_refresh_blocklist': (
            GObject.SignalFlags.RUN_LAST,
            None,
            (str,)
        )
    }


class ConfManager(metaclass=Singleton):

    _background_color = None

    BASE_SCHEMA = {
        'feeds': {},
        'dark_mode': False,
        'reader_theme': 'auto',  # 'auto', 'light', 'dark'
        'new_first': True,
        'windowsize': {
            'width': 350,
            'height': 650
        },
        'max_article_age_days': 30,
        'enable_js': False,
        'max_refresh_threads': 2,
        'read_items': [],
        'show_read_items': True,
        'show_empty_feeds': False,
        'full_article_title': True,
        # valid values: 'webview', 'reader', 'rsscont'
        'default_view': 'webview',
        'open_links_externally': True,
        'full_feed_name': False,
        'refresh_on_startup': False,
        'tags': [],
        'open_youtube_externally': False,
        'media_player': 'mpv',
        'show_thumbnails': True,
        'use_experimental_listview': False,
        'auto_refresh_enabled': False,
        'notify_new_articles': True,
        'auto_refresh_time_seconds': 300,
        'enable_adblock': True,
        'blocklist_last_update': 0.0,
        'webview_zoom': 1.0,
        'font_use_system_for_titles': False,
        'font_use_system_for_paragraphs': True,
        'font_titles_custom': 'DejaVu Serif',
        'font_paragraphs_custom': 'Cantarell',
        'font_monospace_custom': 'DejaVu Sans Mono'
    }

    def __init__(self):
        self.signaler = ConfManagerSignaler()
        self.emit = self.signaler.emit
        self.connect = self.signaler.connect

        self.is_flatpak = isfile('/.flatpak-info')

        self.conf_dir = Path(
            Env.get('XDG_CONFIG_HOME') or f'{Env.get("HOME")}/.config'
        )
        self.cache_home = Path(
            Env.get('XDG_CACHE_HOME') or f'{Env.get("HOME")}/.cache'
        )
        self.cache_path = self.cache_home.joinpath('org.gabmus.gfeeds')
        self.thumbs_cache_path = self.cache_path.joinpath('thumbnails')
        for p in [
                self.conf_dir,
                self.cache_path,
                self.thumbs_cache_path,
        ]:
            if not p.is_dir():
                p.mkdir(parents=True)
        self.path = self.conf_dir.joinpath('org.gabmus.gfeeds.json')

        if self.path.is_file():
            try:
                with open(self.path) as fd:
                    self.conf = json.loads(fd.read())
                # verify that the file has all of the schema keys
                for k in ConfManager.BASE_SCHEMA:
                    if k not in self.conf.keys():
                        if isinstance(
                                ConfManager.BASE_SCHEMA[k], (list, dict)
                        ):
                            self.conf[k] = ConfManager.BASE_SCHEMA[k].copy()
                        else:
                            self.conf[k] = ConfManager.BASE_SCHEMA[k]
                if isinstance(self.conf['feeds'], list):
                    n_feeds = {}
                    for o_feed in self.conf['feeds']:
                        n_feeds[o_feed] = {}
                    self.conf['feeds'] = n_feeds
                    self.save_conf()
            except Exception:
                self.conf = ConfManager.BASE_SCHEMA.copy()
                self.save_conf(force_overwrite=True)
        else:
            self.conf = ConfManager.BASE_SCHEMA.copy()
            self.save_conf()

        bl_gsettings = Gio.Settings.new('org.gnome.desktop.wm.preferences')
        bl = bl_gsettings.get_value('button-layout').get_string()
        self.wm_decoration_on_left = (
            'close:' in bl or
            'maximize:' in bl or
            'minimize:' in bl
        )

        # font_gsettings = Gio.Settings.new('org.gnome.destkop.interface')
        # self.sans_font = font_gsettings.get_value(
        #     'font-name'
        # ).get_string()
        # self.serif_font = font_gsettings.get_value(
        #     'document-font-name'
        # ).get_string()
        # self.mono_font = font_gsettings.get_value(
        #     'monospace-font-name'
        # ).get_string()

        self.article_thumb_cache_path = self.thumbs_cache_path.joinpath(
            'article_thumb_cache.json'
        )
        if not self.article_thumb_cache_path.is_file():
            self.article_thumb_cache = dict()
            self.save_article_thumb_cache()
        else:
            with open(self.article_thumb_cache_path, 'r') as fd:
                self.article_thumb_cache = json.loads(fd.read())

    def save_article_thumb_cache(self):
        with open(self.article_thumb_cache_path, 'w') as fd:
            fd.write(json.dumps(self.article_thumb_cache))

    @property
    def max_article_age(self) -> timedelta:
        return timedelta(days=self.conf['max_article_age_days'])

    def add_tag(self, tag: str, target_feeds=[]):
        lowercase_tags = [t.lower() for t in self.conf['tags']]
        if tag.lower() not in lowercase_tags:
            self.conf['tags'].append(tag)
            self.emit('gfeeds_tags_append', tag)
        for feed in target_feeds:
            if 'tags' not in self.conf['feeds'][feed].keys():
                self.conf['feeds'][feed]['tags'] = []
            if tag not in self.conf['feeds'][feed]['tags']:
                self.conf['feeds'][feed]['tags'].append(tag)
        self.save_conf()

    def delete_tag(self, tag: str):
        while tag in self.conf['tags']:
            self.conf['tags'].remove(tag)
        self.emit('gfeeds_tags_pop', tag)
        self.remove_tag(tag, self.conf['feeds'].keys())
        # self.save_conf()  # done by remove_tags

    def remove_tag(self, tag: str, target_feeds: list):
        for feed in target_feeds:
            if 'tags' not in self.conf['feeds'][feed].keys():
                continue
            if tag in self.conf['feeds'][feed]['tags']:
                self.conf['feeds'][feed]['tags'].remove(tag)
        self.save_conf()

    def __save_conf(self, force_overwrite: bool = False):
        if self.path.is_file() and not force_overwrite:
            with open(self.path, 'r') as fd:
                if json.loads(fd.read()) == self.conf:
                    return
        with open(self.path, 'w') as fd:
            fd.write(json.dumps(self.conf))

    def save_conf(
            self, force_overwrite: bool = False, force_sync: bool = False
    ):
        if force_sync:
            return self.__save_conf(force_overwrite)
        Thread(target=self.__save_conf, args=(force_overwrite,)).start()
