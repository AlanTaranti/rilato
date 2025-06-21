from pathlib import Path
from os.path import isfile
import json
from datetime import timedelta
from gi.repository import GObject
from rilato.conf_mapper import ConfMapper
from rilato.gsettings_wrapper import GsettingsWrapper
from rilato.signal_helper import signal_tuple
from rilato.util.paths import (
    ARTICLE_THUMB_CACHE_PATH,
    CACHE_HOME,
    CACHE_PATH,
    CONF_DIR,
    THUMBS_CACHE_PATH,
)
from rilato.util.singleton import Singleton


class ConfManagerSignaler(GObject.Object):
    __gsignals__ = {
        "rilato_new_first_changed": signal_tuple(),
        "rilato_repopulation_required": signal_tuple(),
        "rilato_webview_settings_changed": signal_tuple(),
        "rilato_show_read_changed": signal_tuple(),
        "rilato_full_article_title_changed": signal_tuple(),
        "rilato_show_empty_feeds_changed": signal_tuple(),
        "rilato_full_feed_name_changed": signal_tuple(),
        "dark_mode_changed": signal_tuple(),
        "show_thumbnails_changed": signal_tuple(),
        "on_apply_adblock_changed": signal_tuple(),
        "on_refresh_blocklist": signal_tuple(),
        # Signals down here don't have to do with the config
        "rilato_filter_changed": signal_tuple(params=(GObject.TYPE_PYOBJECT,)),
        "rilato_tags_append": signal_tuple(params=(str,)),
        "rilato_tags_pop": signal_tuple(params=(str,)),
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
        if k == "windowsize":
            gw["window_width"] = conf[k]["width"]
            gw["window_height"] = conf[k]["height"]
            continue
        try:
            gw[k] = conf[k]
        except KeyError:
            print(f"json_to_gsettings: skipping unsupported key {k}")

    path.unlink()


class ConfManager(metaclass=Singleton):
    def __init__(self):
        self.signaler = ConfManagerSignaler()
        self.emit = self.signaler.emit
        self.connect = self.signaler.connect

        self.is_flatpak = isfile("/.flatpak-info")

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
        self.legacy_conf_path = self.conf_dir.joinpath("org.gabmus.rilato.json")

        self.gsettings_conf = GsettingsWrapper("org.gabmus.rilato")
        self.conf = self.gsettings_conf
        self.nconf = ConfMapper(self.gsettings_conf)
        json_to_gsettings(self.gsettings_conf, self.legacy_conf_path)

        self.article_thumb_cache_path = ARTICLE_THUMB_CACHE_PATH
        if not self.article_thumb_cache_path.is_file():
            self.article_thumb_cache = dict()
            self.save_article_thumb_cache()
        else:
            with open(self.article_thumb_cache_path, "r") as fd:
                self.article_thumb_cache = json.loads(fd.read())

    def save_article_thumb_cache(self):
        with open(self.article_thumb_cache_path, "w") as fd:
            fd.write(json.dumps(self.article_thumb_cache))

    @property
    def max_article_age(self) -> timedelta:
        return timedelta(days=self.nconf.max_article_age_days)

    def add_tag(self, tag: str, target_feeds=[]):
        tags = self.nconf.tags
        lowercase_tags = [t.lower() for t in tags]
        if tag.lower() not in lowercase_tags:
            tags.append(tag)
            self.nconf.tags = tags
            self.emit("rilato_tags_append", tag)
        feeds = self.nconf.feeds
        for feed in target_feeds:
            if "tags" not in feeds[feed].keys():
                feeds[feed]["tags"] = []
            if tag not in feeds[feed]["tags"]:
                feeds[feed]["tags"].append(tag)
        self.nconf.feeds = feeds

    def delete_tag(self, tag: str):
        tags = self.nconf.tags
        while tag in tags:
            tags.remove(tag)
        self.emit("rilato_tags_pop", tag)
        self.nconf.tags = tags
        self.remove_tag(tag, self.nconf.feeds.keys())

    def remove_tag(self, tag: str, target_feeds: list):
        feeds: dict = self.nconf.feeds
        for feed in target_feeds:
            if "tags" not in feeds[feed].keys():
                continue
            if tag in feeds[feed]["tags"]:
                feeds[feed].remove(tag)
        self.nconf.feeds = feeds

    # TODO: legacy; remove
    def save_conf(self, *_):
        pass
