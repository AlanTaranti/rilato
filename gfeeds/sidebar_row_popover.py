from gettext import gettext as _
from gi.repository import Gtk
from gfeeds.confManager import ConfManager
from gfeeds.feeds_manager import FeedsManager


@Gtk.Template(resource_path='/org/gabmus/gfeeds/ui/row_popover.ui')
class RowPopover(Gtk.Popover):
    __gtype_name__ = 'RowPopover'
    read_unread_btn = Gtk.Template.Child()
    read_unread_img = Gtk.Template.Child()
    read_unread_label = Gtk.Template.Child()

    def __init__(self, parent, **kwargs):
        super().__init__(**kwargs)
        self.confman = ConfManager()
        self.feedman = FeedsManager()

        self.parent_w = parent

        self.set_parent(self.parent_w)

    def on_feed_item_set(self):
        if self.parent_w.feed_item is None:
            return
        if self.parent_w.feed_item.read:
            self.read_unread_img.set_from_icon_name(
                'eye-not-looking-symbolic'
            )
            self.read_unread_label.set_text(_(
                'Mark as unread'
            ))
        else:
            self.read_unread_img.set_from_icon_name(
                'eye-open-negative-filled-symbolic'
            )
            self.read_unread_label.set_text(_(
                'Mark as read'
            ))

    def set_read(self, read):
        sidebar = self.parent_w.get_root().leaflet.sidebar
        row = self.parent_w
        if not read:
            row.set_read(False)
            row.popover.read_unread_img.set_from_icon_name(
                'eye-open-negative-filled-symbolic'
            )
            row.popover.read_unread_label.set_text(_(
                'Mark as read'
            ))
        else:
            row.set_read(True)
            row.popover.read_unread_img.set_from_icon_name(
                'eye-not-looking-symbolic'
            )
            row.popover.read_unread_label.set_text(_(
                'Mark as unread'
            ))
        sidebar.listview_sw.invalidate_filter()

    @Gtk.Template.Callback()
    def on_read_unread_clicked(self, btn):
        self.popdown()
        self.set_read(not self.parent_w.feed_item.read)
