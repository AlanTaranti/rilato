from gi.repository import Gtk, Gdk, Gio
from gfeeds.confManager import ConfManager


class PictureView(Gtk.Widget):
    def __init__(self, path):
        super().__init__(
            overflow=Gtk.Overflow.HIDDEN, vexpand=False,
            hexpand=True,
            valign=Gtk.Align.CENTER
        )
        for c in ('frame', 'picture-rounded'):
            self.get_style_context().add_class(c)
        self.confman = ConfManager()
        self.confman.connect(
            'on_max_picture_height_changed',
            lambda *args: self.queue_resize()
        )
        self.texture = None
        self.set_file(path)

    def get_texture(self):
        if self.texture is None:
            self.texture = Gdk.Texture.new_from_file(
                Gio.File.new_for_path(self.path)
            )
        return self.texture

    def drop_cache(self):
        if self.texture:
            del self.texture
            self.texture = None

    def open_image(self, *args):
        if self.open_media_func is not None:
            self.open_media_func()

    def set_file(self, path):
        self.path = path
        self.texture = self.get_texture()
        self.aspect_ratio = self.texture.get_intrinsic_aspect_ratio()
        self.queue_draw()
        self.queue_resize()

    def do_get_request_mode(self, *args):
        return Gtk.SizeRequestMode.HEIGHT_FOR_WIDTH

    def do_snapshot(self, snapshot):
        width = self.get_width()
        height = width / self.aspect_ratio
        self.get_texture().snapshot(
            snapshot,
            width, height
        )
        self.drop_cache()

    def get_real_size(self, w, h):
        meas_w = self.measure(Gtk.Orientation.HORIZONTAL, h)
        w = min(meas_w[1], max(w, meas_w[0]))
        h = self.measure(Gtk.Orientation.VERTICAL, w)[0]
        return w, h

    def do_measure(self, orientation, for_size):
        if orientation == Gtk.Orientation.VERTICAL:
            # max prevents the height to be lower than the minimum
            # that I defined
            height = min(
                for_size / self.aspect_ratio,
                max(self.confman.conf['max_picture_height'], 100)
            )
            return (height, height, -1, -1)
        else:
            return (
                1,
                1200,
                -1, -1
            )
