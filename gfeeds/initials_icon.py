from gi.repository import Gtk, Handy, GdkPixbuf
from gfeeds.confManager import ConfManager
from pathlib import Path
from PIL import Image


confman = ConfManager()
thumbs_cache_path = Path(confman.thumbs_cache_path)


def make_thumb(path, width: int, height: int = 1000) -> str:
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


avatar_cache = dict()


def set_avatar_func(icon: str, size: int) -> GdkPixbuf.Pixbuf:
    if icon is None:
        return None
    key = f'{icon}__{size}'
    if key in avatar_cache.keys():
        return avatar_cache[key]
    pixbuf = None
    try:
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(
            make_thumb(icon, size, size)
        )
    except Exception:
        print(f'Error creating pixbuf for icon `{icon}`')
    avatar_cache[key] = pixbuf
    return pixbuf


class InitialsIcon(Gtk.Box):
    def __init__(self, name, image_path, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.image_path = image_path
        self.avatar = Handy.Avatar.new(
            32,
            self.name,
            True
        )
        self.avatar.set_image_load_func(
            lambda size: set_avatar_func(self.image_path, size)
        )
        self.append(self.avatar)
