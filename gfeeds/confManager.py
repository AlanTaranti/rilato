from pathlib import Path
from os.path import isdir
from os import makedirs
from os import environ as Env
import json
from datetime import timedelta
from gi.repository import Gtk, GObject, Gio
from gfeeds.singleton import Singleton
from gfeeds.signaler_list import SignalerList


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
        'on_max_picture_height_changed': (
            GObject.SignalFlags.RUN_LAST,
            None,
            (str,)
        ),
        'show_thumbnails_changed': (
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
        'dark_reader': False,
        'new_first': True,
        'windowsize': {
            'width': 350,
            'height': 650
        },
        'max_article_age_days': 30,
        'enable_js': False,
        'max_refresh_threads': 2,
        'saved_items': {},
        'read_items': [],
        'show_read_items': True,
        'full_article_title': True,
        # valid values: 'webview', 'reader', 'rsscont'
        'default_view': 'webview',
        'open_links_externally': True,
        'full_feed_name': False,
        'refresh_on_startup': False,
        'tags': [],
        'open_youtube_externally': False,
        'media_player': 'mpv',
        'max_picture_height': 600,
        'show_thumbnails': True
    }

    def __init__(self):
        self.window = None
        self.signaler = ConfManagerSignaler()
        self.emit = self.signaler.emit
        self.connect = self.signaler.connect

        self.conf_dir = Env.get("XDG_CONFIG_HOME")
        self.cache_path = Path(
            f'{Env.get("XDG_CACHE_HOME")}/org.gabmus.gfeeds'
        )
        if self.conf_dir is None:
            self.conf_dir = f'{Env.get("HOME")}/.config'
        if self.cache_path is None:
            self.cache_path = Path(
                f'{Env.get("HOME")}/.cache/org.gabmus.gfeeds'
            )
        self.thumbs_cache_path = f'{self.cache_path}/thumbnails/'
        old_saved_cache_path = f'{self.cache_path}/saved_articles'
        self.saved_cache_path = \
            f'{self.conf_dir}/org.gabmus.gfeeds.saved_articles'
        for p in [
                self.conf_dir,
                self.cache_path,
                self.thumbs_cache_path,
                self.saved_cache_path
        ]:
            if not isdir(str(p)):
                makedirs(str(p))
        self.path = Path(
            f'{self.conf_dir}/org.gabmus.gfeeds.json'
        )

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

        # TODO: remove down the road, old saved articles migration
        if isdir(old_saved_cache_path):
            from os import listdir, rmdir
            from shutil import move
            for f in listdir(old_saved_cache_path):
                move(
                    f'{old_saved_cache_path}/{f}',
                    f'{self.saved_cache_path}/{f}'
                )
            rmdir(old_saved_cache_path)

        self.read_feeds_items = SignalerList(self.conf['read_items'])
        self.read_feeds_items.connect(
            'append', self.dump_read_items_to_conf
        )
        self.read_feeds_items.connect(
            'pop', self.dump_read_items_to_conf
        )

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
        print(self.conf['tags'])
        self.remove_tag(tag, self.conf['feeds'].keys())
        # self.save_conf()  # done by remove_tags

    def remove_tag(self, tag: str, target_feeds: list):
        for feed in target_feeds:
            if 'tags' not in self.conf['feeds'][feed].keys():
                continue
            if tag in self.conf['feeds'][feed]['tags']:
                self.conf['feeds'][feed]['tags'].remove(tag)
        self.save_conf()

    def dump_read_items_to_conf(self, *args):
        self.conf['read_items'] = self.read_feeds_items.get_list()

    def save_conf(self, *args, force_overwrite=False):
        if self.path.is_file() and not force_overwrite:
            with open(self.path, 'r') as fd:
                if json.loads(fd.read()) == self.conf:
                    return
        with open(self.path, 'w') as fd:
            fd.write(json.dumps(self.conf))

    def get_background_color(self) -> str:
        if ConfManager._background_color is not None:
            return ConfManager._background_color
        if not self.window:
            return "000000"
        gc = self.window.get_style_context(
                ).get_background_color(Gtk.StateFlags.NORMAL)
        color = ''
        for channel in (gc.red, gc.green, gc.blue):
            color += '%02x' % int(channel*255)
        ConfManager._background_color = color
        return color
