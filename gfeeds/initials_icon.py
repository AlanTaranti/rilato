from gi.repository import Gtk, Adw, GLib, Gdk, Gio
from threading import Thread
from gfeeds.confManager import ConfManager
from pathlib import Path
from PIL import Image
from typing import Union


confman = ConfManager()
thumbs_cache_path = Path(confman.thumbs_cache_path)


def make_thumb(path, width: int, height: int = 1000) -> Union[str, None]:
    if not path:
        return None
    if not isinstance(path, Path):
        path = Path(path)
    dest = thumbs_cache_path.joinpath(f'{width}x{height}_{path.name}_v2')
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
    def __init__(self, size: int, title: str, get_image_func):
        super().__init__(hexpand=False, vexpand=False, halign=Gtk.Align.CENTER)
        self.avatar = Adw.Avatar.new(size, title, True)
        self.set_child(self.avatar)
        self.get_image_func = get_image_func
        self.load_avatar()

    def load_avatar(self, title=None, n_image_func=None):
        if title is not None:
            self.avatar.set_text(title)
        self.avatar.set_custom_image(None)

        def af():
            if n_image_func is not None:
                self.get_image_func = n_image_func
            icon = self.get_image_func()
            if icon is None:
                return
            GLib.idle_add(cb, icon)

        def cb(icon):
            texture = _textures_cache.get(
                icon, Gdk.Texture.new_from_file(
                    Gio.File.new_for_path(icon)
                )
            )
            if icon not in _textures_cache.keys():
                _textures_cache[icon] = texture
            self.avatar.set_custom_image(texture)

        Thread(target=af, daemon=True).start()


class InitialsIcon(SimpleAvatar):
    def __init__(self, name: str, image_path):
        super().__init__(32, name, lambda: make_thumb(image_path, 32, 32))
