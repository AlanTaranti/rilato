from gettext import gettext as _
from gi.repository import Gtk


def GFeedsOpmlFileChooserDialog(parent_window):
    dialog = Gtk.FileChooserNative.new(
        _('Choose an OPML file to import'),
        parent_window,
        Gtk.FileChooserAction.OPEN,
        Gtk.STOCK_OPEN,
        Gtk.STOCK_CANCEL
    )
    dialog.set_transient_for(parent_window)
    dialog.set_modal(True)
    f_filter = Gtk.FileFilter()
    f_filter.set_name(_('XML files'))
    f_filter.add_mime_type('text/xml')
    dialog.set_filter(f_filter)
    return dialog


def GFeedsOpmlSavePathChooserDialog(parent_window):
    dialog = Gtk.FileChooserNative.new(
        _('Choose where to save the exported OPML file'),
        parent_window,
        Gtk.FileChooserAction.SAVE,
        Gtk.STOCK_SAVE,
        Gtk.STOCK_CANCEL
    )
    dialog.set_transient_for(parent_window)
    dialog.set_modal(True)
    dialog.set_do_overwrite_confirmation(True)
    dialog.set_create_folders(True)
    f_filter = Gtk.FileFilter()
    f_filter.set_name(_('XML files'))
    f_filter.add_mime_type('text/xml')
    dialog.set_filter(f_filter)
    dialog.set_current_name('GFeeds.opml')
    return dialog
