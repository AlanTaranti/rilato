from typing import Dict, List, Literal, cast
from rilato.gsettings_wrapper import GSETTINGS_TYPES, GsettingsWrapper


class ConfMapper:
    def __init__(self, gsw: GsettingsWrapper):
        self.gsw = gsw

    @property
    def feeds(
        self,
    ) -> Dict[str, Dict[Literal["tags", "last-modified"], List[str] | str]]:
        return cast(dict, self.gsw.get("feeds"))

    @feeds.setter
    def feeds(self, nval: dict):
        self.set("feeds", nval)

    @property
    def dark_mode(self) -> bool:
        return cast(bool, self.gsw.raw_get("dark-mode"))

    @dark_mode.setter
    def dark_mode(self, nval: bool):
        self.set("dark_mode", nval)

    @property
    def reader_theme(self) -> Literal["auto", "light", "dark"]:
        return cast(Literal["auto", "light", "dark"], self.gsw.raw_get("reader-theme"))

    @reader_theme.setter
    def reader_theme(self, nval: Literal["auto", "light", "dark"]):
        self.set("reader_theme", nval)

    @property
    def new_first(self) -> bool:
        return cast(bool, self.gsw.raw_get("new-first"))

    @new_first.setter
    def new_first(self, nval: bool):
        self.set("new_first", nval)

    @property
    def window_height(self) -> int:
        return cast(int, self.gsw.raw_get("window-height"))

    @window_height.setter
    def window_height(self, nval: int):
        self.set("window_height", nval)

    @property
    def window_width(self) -> int:
        return cast(int, self.gsw.raw_get("window-width"))

    @window_width.setter
    def window_width(self, nval: int):
        self.set("window_width", nval)

    @property
    def max_article_age_days(self) -> int:
        return cast(int, self.gsw.raw_get("max-article-age-days"))

    @max_article_age_days.setter
    def max_article_age_days(self, nval: int):
        self.set("max_article_age_days", nval)

    @property
    def enable_js(self) -> bool:
        return cast(bool, self.gsw.raw_get("enable-js"))

    @enable_js.setter
    def enable_js(self, nval: bool):
        self.set("enable_js", nval)

    @property
    def max_refresh_threads(self) -> int:
        return cast(int, self.gsw.raw_get("max-refresh-threads"))

    @max_refresh_threads.setter
    def max_refresh_threads(self, nval: int):
        self.set("max_refresh_threads", nval)

    @property
    def read_items(self) -> List[str]:
        return cast(List[str], self.gsw.raw_get("read-items"))

    @read_items.setter
    def read_items(self, nval: List[str]):
        self.set("read_items", nval)

    @property
    def show_read_items(self) -> bool:
        return cast(bool, self.gsw.raw_get("show-read-items"))

    @show_read_items.setter
    def show_read_items(self, nval: bool):
        self.set("show_read_items", nval)

    @property
    def show_empty_feeds(self) -> bool:
        return cast(bool, self.gsw.raw_get("show-empty-feeds"))

    @show_empty_feeds.setter
    def show_empty_feeds(self, nval: bool):
        self.set("show_empty_feeds", nval)

    @property
    def full_article_title(self) -> bool:
        return cast(bool, self.gsw.raw_get("full-article-title"))

    @full_article_title.setter
    def full_article_title(self, nval: bool):
        self.set("full_article_title", nval)

    @property
    def default_view(self) -> Literal["webview", "reader", "feedcont"]:
        return cast(
            Literal["webview", "reader", "feedcont"], self.gsw.raw_get("default-view")
        )

    @default_view.setter
    def default_view(self, nval: Literal["webview", "reader", "feedcont"]):
        self.set("default_view", nval)

    @property
    def open_links_externally(self) -> bool:
        return cast(bool, self.gsw.raw_get("open-links-externally"))

    @open_links_externally.setter
    def open_links_externally(self, nval: bool):
        self.set("open_links_externally", nval)

    @property
    def full_feed_name(self) -> bool:
        return cast(bool, self.gsw.raw_get("full-feed-name"))

    @full_feed_name.setter
    def full_feed_name(self, nval: bool):
        self.set("full_feed_name", nval)

    @property
    def refresh_on_startup(self) -> bool:
        return cast(bool, self.gsw.raw_get("refresh-on-startup"))

    @refresh_on_startup.setter
    def refresh_on_startup(self, nval: bool):
        self.set("refresh_on_startup", nval)

    @property
    def tags(self) -> List[str]:
        return cast(List[str], self.gsw.raw_get("tags"))

    @tags.setter
    def tags(self, nval: List[str]):
        self.set("tags", nval)

    @property
    def open_youtube_externally(self) -> bool:
        return cast(bool, self.gsw.raw_get("open-youtube-externally"))

    @open_youtube_externally.setter
    def open_youtube_externally(self, nval: bool):
        self.set("open_youtube_externally", nval)

    @property
    def media_player(self) -> str:
        return cast(str, self.gsw.raw_get("media-player"))

    @media_player.setter
    def media_player(self, nval: str):
        self.set("media_player", nval)

    @property
    def show_thumbnails(self) -> bool:
        return cast(bool, self.gsw.raw_get("show-thumbnails"))

    @show_thumbnails.setter
    def show_thumbnails(self, nval: bool):
        self.set("show_thumbnails", nval)

    @property
    def use_experimental_listview(self) -> bool:
        return cast(bool, self.gsw.raw_get("use-experimental-listview"))

    @use_experimental_listview.setter
    def use_experimental_listview(self, nval: bool):
        self.set("use_experimental_listview", nval)

    @property
    def auto_refresh_enabled(self) -> bool:
        return cast(bool, self.gsw.raw_get("auto-refresh-enabled"))

    @auto_refresh_enabled.setter
    def auto_refresh_enabled(self, nval: bool):
        self.set("auto_refresh_enabled", nval)

    @property
    def notify_new_articles(self) -> bool:
        return cast(bool, self.gsw.raw_get("notify-new-articles"))

    @notify_new_articles.setter
    def notify_new_articles(self, nval: bool):
        self.set("notify_new_articles", nval)

    @property
    def auto_refresh_time_seconds(self) -> int:
        return cast(int, self.gsw.raw_get("auto-refresh-time-seconds"))

    @auto_refresh_time_seconds.setter
    def auto_refresh_time_seconds(self, nval: int):
        self.set("auto_refresh_time_seconds", nval)

    @property
    def enable_adblock(self) -> bool:
        return cast(bool, self.gsw.raw_get("enable-adblock"))

    @enable_adblock.setter
    def enable_adblock(self, nval: bool):
        self.set("enable_adblock", nval)

    @property
    def blocklist_last_update(self) -> float:
        return cast(float, self.gsw.raw_get("blocklist-last-update"))

    @blocklist_last_update.setter
    def blocklist_last_update(self, nval: float):
        self.set("blocklist_last_update", nval)

    @property
    def webview_zoom(self) -> float:
        return cast(float, self.gsw.raw_get("webview-zoom"))

    @webview_zoom.setter
    def webview_zoom(self, nval: float):
        self.set("webview_zoom", nval)

    @property
    def font_use_system_for_titles(self) -> bool:
        return cast(bool, self.gsw.raw_get("font-use-system-for-titles"))

    @font_use_system_for_titles.setter
    def font_use_system_for_titles(self, nval: bool):
        self.set("font_use_system_for_titles", nval)

    @property
    def font_use_system_for_paragraphs(self) -> bool:
        return cast(bool, self.gsw.raw_get("font-use-system-for-paragraphs"))

    @font_use_system_for_paragraphs.setter
    def font_use_system_for_paragraphs(self, nval: bool):
        self.set("font_use_system_for_paragraphs", nval)

    @property
    def font_titles_custom(self) -> str:
        return cast(str, self.gsw.raw_get("font-titles-custom"))

    @font_titles_custom.setter
    def font_titles_custom(self, nval: str):
        self.set("font_titles_custom", nval)

    @property
    def font_paragraphs_custom(self) -> str:
        return cast(str, self.gsw.raw_get("font-paragraphs-custom"))

    @font_paragraphs_custom.setter
    def font_paragraphs_custom(self, nval: str):
        self.set("font_paragraphs_custom", nval)

    @property
    def font_monospace_custom(self) -> str:
        return cast(str, self.gsw.raw_get("font-monospace-custom"))

    @font_monospace_custom.setter
    def font_monospace_custom(self, nval: str):
        self.set("font_monospace_custom", nval)

    def set(self, key: str, val: GSETTINGS_TYPES):
        self.gsw.set(key, val)
