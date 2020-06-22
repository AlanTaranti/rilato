from xml.sax.saxutils import escape
from gettext import gettext as _
from gi.repository import Gtk
from gfeeds.opml_manager import opml_to_rss_list
from gfeeds.scrolled_message_dialog import ScrolledMessageDialog


class GFeedsConfirmAddDialog(ScrolledMessageDialog):
    def __init__(self, parent, f_path, http=False, **kwargs):
        super().__init__(
            parent,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            Gtk.MessageType.QUESTION,
            Gtk.ButtonsType.YES_NO,
            (
                _('Do you want to import these feeds?') if not http
                else _('Do you want to import this feed?')
            ),
            **kwargs
        )

        if not http:
            self.format_secondary_markup(
                escape([f['feed'] for f in opml_to_rss_list(f_path)])
            )
        else:
            self.format_secondary_markup(
                escape(f_path)
            )
