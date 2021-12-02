from gi.repository import Gtk, Gdk, Gio, GLib
from gfeeds.confManager import ConfManager
from threading import Thread
from math import ceil

class PictureView(Gtk.Widget):
    def __init__(self, path):
        super().__init__(
            overflow=Gtk.Overflow.HIDDEN, vexpand=True,
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

    def set_file(self, path):
        self.path = path
        if self.path is None:
            self.texture = None
            return
        gio_file = Gio.File.new_for_path(self.path)

        def af():
            try:
                self.texture = Gdk.Texture.new_from_file(gio_file)
            except Exception:
                print(
                    f'PictureView: Error creating texture for `{self.path}`'
                )
                self.texture = None
            GLib.idle_add(cb)

        def cb():
            if self.texture is None:
                return
            self.queue_draw()
            self.queue_resize()

        Thread(target=af, daemon=True).start()

    def do_get_request_mode(self, *args):
        return Gtk.SizeRequestMode.HEIGHT_FOR_WIDTH

    def do_snapshot(self, snapshot):
        if self.texture is None:
            return
        width = self.get_width()
        height = width / self.texture.get_intrinsic_aspect_ratio()
        self.texture.snapshot(
            snapshot,
            width, height
        )

    def do_measure(self, orientation, for_size):
        if not self.texture:
            return (0, 1200, -1, -1)
        if orientation == Gtk.Orientation.VERTICAL:  # get height
            if for_size == -1:
                return (1200, 1200, -1, -1)
            cw, ch = self.texture.compute_concrete_size(
                for_size, 0, 1200, 1200
            )
            # nat = max(self.confman.conf['max_picture_height'], 100)
            ch = min(ch, 1200)
            return (ch, 1200, -1, -1)
        else:  # get width
            return (0, 1200, -1, -1)
