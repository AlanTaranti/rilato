from gi.repository import Gtk, Gdk, Gio, GLib
from gfeeds.confManager import ConfManager
from threading import Thread


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
        self.aspect_ratio = None
        self.set_file(path)

    def set_file(self, path):
        self.path = path
        if self.path is None:
            self.texture = None
            self.aspect_ratio = None
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
            self.aspect_ratio = self.texture.get_intrinsic_aspect_ratio()
            self.queue_draw()
            self.queue_resize()

        Thread(target=af, daemon=True).start()

    def do_get_request_mode(self, *args):
        return Gtk.SizeRequestMode.HEIGHT_FOR_WIDTH

    def do_snapshot(self, snapshot):
        if self.texture is None or self.aspect_ratio is None:
            return
        width = self.get_width()
        height = width / self.aspect_ratio
        self.texture.snapshot(
            snapshot,
            width, height
        )

    def get_real_size(self, w, h):
        meas_w = self.measure(Gtk.Orientation.HORIZONTAL, h)
        w = min(meas_w[1], max(w, meas_w[0]))
        h = self.measure(Gtk.Orientation.VERTICAL, w)[0]
        return w, h

    def do_measure(self, orientation, for_size):
        if self.aspect_ratio is None:
            return (0, 0, -1, -1)
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
