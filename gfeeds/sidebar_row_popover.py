from gettext import gettext as _
from gi.repository import Gtk
from gfeeds.confManager import ConfManager
from gfeeds.feeds_manager import FeedsManager


class RowPopover(Gtk.Popover):
    def __init__(self, parent, **kwargs):
        super().__init__(**kwargs)
        self.confman = ConfManager()
        self.feedman = FeedsManager()
        self.builder = Gtk.Builder.new_from_resource(
            '/org/gabmus/gfeeds/ui/article_right_click_popover_content.ui'
        )
        self.container_box = self.builder.get_object('container_box')
        self.parent_w = parent

        self.read_unread_btn = self.builder.get_object('read_unread_btn')
        self.read_unread_btn.connect('clicked', self.on_read_unread_clicked)
        self.read_unread_img = self.builder.get_object('read_unread_img')
        self.read_unread_label = self.builder.get_object('read_unread_label')

        self.set_autohide(True)
        self.set_parent(self.parent_w)
        self.set_child(self.container_box)

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

    def on_read_unread_clicked(self, btn):
        self.popdown()
        self.set_read(not self.parent_w.feed_item.read)
