from xml.sax.saxutils import escape
from gettext import gettext as _
from gi.repository import Gtk
from gfeeds.opml_manager import opml_to_rss_list
from gfeeds.scrolled_message_dialog import ScrolledMessageDialog


class GFeedsConfirmAddDialog(ScrolledMessageDialog):
    def __init__(self, parent, f_path, http=False, **kwargs):
        super().__init__(
            transient_for=parent,
            modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=(
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
