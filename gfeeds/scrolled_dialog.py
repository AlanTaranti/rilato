from typing import Optional
from gi.repository import Gtk, GObject


@Gtk.Template(resource_path='/org/gabmus/gfeeds/ui/scrolled_dialog.ui')
class ScrolledDialog(Gtk.Window):
    __gtype_name__ = 'ScrolledDialog'
    __gsignals__ = {
        'response': (
            GObject.SignalFlags.RUN_LAST,
            None,
            (Gtk.ResponseType,)
        )
    }
    title_label: Gtk.Label = Gtk.Template.Child()
    message_label: Gtk.Label = Gtk.Template.Child()

    def __init__(
            self, transient_for: Gtk.Window, title: Optional[str] = None,
            message: Optional[str] = None
    ):
        super().__init__(
            modal=True, transient_for=transient_for
        )
        for txt, label in (
                (title, self.title_label), (message, self.message_label)
        ):
            if txt is not None:
                label.set_text(txt)

    @Gtk.Template.Callback()
    def on_yes_clicked(self, _):
        self.emit('response', Gtk.ResponseType.YES)

    @Gtk.Template.Callback()
    def on_no_clicked(self, _):
        self.emit('response', Gtk.ResponseType.NO)
