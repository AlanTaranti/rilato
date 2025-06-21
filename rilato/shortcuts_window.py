from gi.repository import Gtk


def show_shortcuts_window(parent_win, *args):
    shortcuts_win = Gtk.Builder.new_from_resource(
        '/org/gabmus/rilato/ui/shortcutsWindow.ui'
    ).get_object('shortcuts-rilato')
    shortcuts_win.set_transient_for(parent_win)
    shortcuts_win.present()
