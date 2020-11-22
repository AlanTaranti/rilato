from gettext import gettext as _
from gi.repository import Gtk


class RefreshSpinnerButton(Gtk.Box):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.builder = Gtk.Builder.new_from_resource(
            '/org/gabmus/gfeeds/ui/spinner_button.glade'
        )
        self.btn = self.builder.get_object('spinnerbutton')
        self.stack = self.builder.get_object('stack')
        self.spinner = self.builder.get_object('spinner')
        self.icon = self.builder.get_object('icon')

        self.btn.set_tooltip_text(_('Refresh feeds'))
        self.append(self.btn)
        self.stack.set_visible_child(self.icon)

    def set_spinning(self, state):
        if state:
            self.stack.set_visible_child(self.spinner)
            self.btn.set_sensitive(False)
        else:
            self.stack.set_visible_child(self.icon)
            self.btn.set_sensitive(True)
