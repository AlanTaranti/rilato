from gi.repository import Gtk


class RevealerLoadingBar(Gtk.Revealer):
    def __init__(self):
        super().__init__(transition_type=Gtk.RevealerTransitionType.CROSSFADE)

        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.get_style_context().add_class('osd')
        self.set_child(self.progress_bar)
        self.set_fraction = self.progress_bar.set_fraction
        self.set_reveal_child(True)
