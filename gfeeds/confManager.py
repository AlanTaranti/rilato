from pathlib import Path
from os.path import isfile
import json
from datetime import timedelta
from typing import List
from gi.repository import GObject
from gfeeds.gsettings_wrapper import GsettingsWrapper
from gfeeds.util.paths import (
    ARTICLE_THUMB_CACHE_PATH,
    CACHE_HOME,
    CACHE_PATH,
    CONF_DIR,
    THUMBS_CACHE_PATH
)
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


def json_to_gsettings(gw: GsettingsWrapper, path: Path):
    conf = dict()

    if path.is_file():
        try:
            with open(path) as fd:
                conf = json.loads(fd.read())
        except Exception:
            return
    else:
        return

    for k in conf.keys():
        if k == 'windowsize':
            gw['window_width'] = conf[k]['width']
            gw['window_height'] = conf[k]['height']
            continue
        try:
            gw[k] = conf[k]
        except KeyError:
            print(f'json_to_gsettings: skipping unsupported key {k}')

    path.unlink()


class ConfManager(metaclass=Singleton):
    def __init__(self):
        self.signaler = ConfManagerSignaler()
        self.emit = self.signaler.emit
        self.connect = self.signaler.connect

        self.is_flatpak = isfile('/.flatpak-info')

        self.conf_dir = CONF_DIR
        self.cache_home = CACHE_HOME
        self.cache_path = CACHE_PATH
        self.thumbs_cache_path = THUMBS_CACHE_PATH
        for p in [
                self.conf_dir,
                self.cache_path,
                self.thumbs_cache_path,
        ]:
            if not p.is_dir():
                p.mkdir(parents=True)
        self.legacy_conf_path = self.conf_dir.joinpath(
            'org.gabmus.gfeeds.json'
        )

        self.conf = GsettingsWrapper('org.gabmus.gfeeds')
        json_to_gsettings(self.conf, self.legacy_conf_path)

        self.article_thumb_cache_path = ARTICLE_THUMB_CACHE_PATH
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
        tags: list = self.conf['tags']
        lowercase_tags = [t.lower() for t in tags]
        if tag.lower() not in lowercase_tags:
            tags.append(tag)
            self.conf['tags'] = tags
            self.emit('gfeeds_tags_append', tag)
        feeds: dict = self.conf['feeds']
        for feed in target_feeds:
            if 'tags' not in feeds[feed].keys():
                feeds[feed]['tags'] = []
            if tag not in feeds[feed]['tags']:
                feeds[feed]['tags'].append(tag)
        self.conf['feeds'] = feeds

    def delete_tag(self, tag: str):
        tags: List[str] = self.conf['tags']
        while tag in tags:
            tags.remove(tag)
        self.emit('gfeeds_tags_pop', tag)
        self.conf['tags'] = tags
        self.remove_tag(tag, self.conf['feeds'].keys())

    def remove_tag(self, tag: str, target_feeds: list):
        feeds: dict = self.conf['feeds']
        for feed in target_feeds:
            if 'tags' not in feeds[feed].keys():
                continue
            if tag in feeds[feed]['tags']:
                feeds[feed].remove(tag)
        self.conf['feeds'] = feeds

    # TODO: legacy; remove
    def save_conf(self, *_):
        pass
