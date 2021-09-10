from gi.repository import Gtk


class RevealerLoadingBar(Gtk.Revealer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.progress_bar = Gtk.ProgressBar()
        self.set_child(self.progress_bar)
        self.set_fraction = self.progress_bar.set_fraction
        self.set_reveal_child(True)
