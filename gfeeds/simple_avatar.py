from gi.repository import Adw, GLib, Gdk, Gio
from threading import Thread
from pathlib import Path
from os.path import isfile
from PIL import Image
from typing import Union
from gfeeds.util.paths import THUMBS_CACHE_PATH


def make_thumb(path, width: int, height: int = 1000) -> Union[str, None]:
    if not path:
        return None
    if not isinstance(path, Path):
        path = Path(path)
    dest = THUMBS_CACHE_PATH.joinpath(f'{width}x{height}_{path.name}_v2')
    if dest.is_file():
        return str(dest)
    try:
        with Image.open(path) as thumb:
            thumb = Image.open(path)
            thumb.resize((width, height)).save(dest, 'PNG')
            # thumb.thumbnail((width, height), Image.ANTIALIAS)
            # thumb.save(dest, 'PNG')
        return str(dest)
    except IOError:
        print(f'Error creating thumbnail for image `{path}`')
        return None


_textures_cache = dict()


class SimpleAvatar(Adw.Bin):
    def __init__(self):
        super().__init__()
        self.avatar = Adw.Avatar(size=32, show_initials=True)
        self.set_child(self.avatar)

    def set_image(self, title, image=None):
        self.avatar.set_text(title)
        if not image:
            return
        if not isfile(image):
            _textures_cache[image] = None

        def cb(texture, add_to_cache=False):
            if add_to_cache:
                _textures_cache[image] = texture
            self.avatar.set_custom_image(texture)

        if image in _textures_cache.keys():
            cached = _textures_cache[image]
            if not cached:
                return
            GLib.idle_add(cb, cached)
            return

        def af():
            gio_file = Gio.File.new_for_path(image)
            try:
                texture = Gdk.Texture.new_from_file(gio_file)
            except Exception:
                print(
                    'SimpleAvatar: '
                    'Error creating texture for `{0}` (title `{1}`)'.format(
                        image, title
                    )
                )
                texture = None
            GLib.idle_add(cb, texture, True)

        Thread(target=af, daemon=True).start()
