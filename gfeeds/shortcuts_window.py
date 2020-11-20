from gi.repository import Gtk


def show_shortcuts_window(parent_win, *args):
    shortcuts_win = Gtk.Builder.new_from_resource(
        '/org/gabmus/gfeeds/ui/shortcutsWindow.xml'
    ).get_object('shortcuts-gfeeds')
    shortcuts_win.props.section_name = 'shortcuts'
    shortcuts_win.set_transient_for(parent_win)
    shortcuts_win.set_modal(True)
    shortcuts_win.present()
    shortcuts_win.show_all()
