from gi.repository import Adw
from gi.repository import Gtk


@Gtk.Template(resource_path="/me/alantaranti/rilato/window.ui")
class RilatoWindow(Adw.ApplicationWindow):
    __gtype_name__ = "RilatoWindow"

    label = Gtk.Template.Child()
    startup_entry = Gtk.Template.Child()
    send_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Clear entry at startup
        self.startup_entry.set_text("")

    @Gtk.Template.Callback
    def on_send_button_clicked(self, widget):
        self._send_input()

    @Gtk.Template.Callback
    def on_startup_entry_activate(self, entry):
        self._send_input()

    def _send_input(self):
        text = self.startup_entry.get_text()
        # TODO: handle sending text
        print(f"Sending input: {text}")
        self.startup_entry.set_text("")
