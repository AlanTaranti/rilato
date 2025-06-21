from os import environ
from pathlib import Path


IS_FLATPAK = Path('/.flatpak-info').is_file()
CONF_DIR = Path(
    environ.get('XDG_CONFIG_HOME') or f'{environ.get("HOME")}/.config'
)
CACHE_HOME = Path(
    environ.get('XDG_CACHE_HOME') or f'{environ.get("HOME")}/.cache'
)
CACHE_PATH = CACHE_HOME.joinpath('org.gabmus.rilato')
THUMBS_CACHE_PATH = CACHE_PATH.joinpath('thumbnails')
ARTICLE_THUMB_CACHE_PATH = THUMBS_CACHE_PATH.joinpath(
    'article_thumb_cache.json'
)

for p in [
        THUMBS_CACHE_PATH,
        CONF_DIR
]:
    if not p.is_dir():
        p.mkdir(parents=True)
