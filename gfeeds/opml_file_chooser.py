from gettext import gettext as _
from gi.repository import Gtk

def get_xml_filter():
    filter = Gtk.FileFilter()
    filter.set_name(_('XML files'))
    filter.add_mime_type('text/xml')
    return filter


def GFeedsOpmlFileChooserDialog(parent_window):
    return Gtk.FileChooserNative(
        title=_('Choose an OPML file to import'),
        transient_for=parent_window,
        modal=True,
        action=Gtk.FileChooserAction.OPEN,
        accept_label=_('Open'),
        cancel_label=_('Cancel'),
        filter=get_xml_filter()
    )

def GFeedsOpmlSavePathChooserDialog(parent_window):
    dialog = Gtk.FileChooserNative(
        title=_('Choose where to save the exported OPML file'),
        transient_for=parent_window,
        modal=True,
        action=Gtk.FileChooserAction.SAVE,
        accept_label=_('Save'),
        cancel_label=_('Cancel'),
        create_folders=True,
        filter=get_xml_filter()
    )
    dialog.set_current_name('GFeeds.opml')
    return dialog
