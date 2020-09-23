from gi.repository import Gtk, Handy, GdkPixbuf
from os.path import isfile


class InitialsIcon(Gtk.Bin):
    def __init__(self, name, image_path, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.image_path = image_path
        self.avatar = Handy.Avatar.new(
            32,
            self.name,
            True
        )
        self.avatar.set_image_load_func(self.__set_avatar_func)
        self.add(self.avatar)

    def __set_avatar_func(self, *args):
        return (
            GdkPixbuf.Pixbuf.new_from_file(self.image_path)
            if isfile(self.image_path) else None
        )
