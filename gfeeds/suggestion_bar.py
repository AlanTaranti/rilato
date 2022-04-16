from gettext import gettext as _
from gi.repository import Gtk, Pango
from gfeeds.feeds_manager import FeedsManager


class GFeedsInfoBar(Gtk.InfoBar):
    def __init__(self, text, icon_name=None,
                 message_type=Gtk.MessageType.INFO, **kwargs):
        super().__init__(hexpand=False, **kwargs)
        self.set_message_type(message_type)
        self.text = text
        self.container_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=6, margin_top=6,
            margin_bottom=6, halign=Gtk.Align.CENTER, hexpand=True
        )
        self.label = Gtk.Label(
            label=self.text, wrap=True, wrap_mode=Pango.WrapMode.WORD_CHAR
        )
        self.label.set_xalign(0.0)
        if icon_name:
            self.icon_name = icon_name
            self.icon = Gtk.Image.new_from_icon_name(
                self.icon_name
            )
            self.container_box.append(self.icon)
        self.container_box.append(self.label)
        self.add_child(self.container_box)
        # self.set_size_request(360, -1)


class GFeedsConnectionBar(GFeedsInfoBar):
    def __init__(self, **kwargs):
        super().__init__(
            text=_('You are offline'),
            icon_name='network-offline-symbolic',
            message_type=Gtk.MessageType.INFO,
            **kwargs
        )
        self.container_box.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.feedman = FeedsManager()
        self.feedman.connect(
            'feedmanager_online_changed',
            lambda caller, value: self.set_revealed(not value)
        )
        self.set_revealed(False)
