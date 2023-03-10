from typing import Optional
from gi.repository import GObject, Gtk, Adw
from gfeeds.feeds_manager import FeedsManager
from gfeeds.confManager import ConfManager


@Gtk.Template(resource_path='/org/gabmus/gfeeds/ui/empty_state.ui')
class EmptyState(Adw.Bin):
    __gtype_name__ = 'EmptyState'

    def __init__(self):
        super().__init__()


class StackWithEmptyState(Gtk.Stack):
    __gtype_name__ = 'StackWithEmptyState'

    def __init__(self, main_widget: Optional[Gtk.Widget] = None):
        super().__init__(
            vexpand=True, hexpand=True,
            transition_type=Gtk.StackTransitionType.CROSSFADE
        )
        self.__main_widget = main_widget
        self.feedman = FeedsManager()
        self.confman = ConfManager()
        self.empty_state = EmptyState()
        if self.main_widget is not None:
            self.add_named(self.main_widget, 'main_widget')
        self.add_named(self.empty_state, 'empty_state')
        self.set_visible_child(
            self.main_widget if len(self.confman.nconf.feeds) > 0
            and self.main_widget is not None
            else self.empty_state
        )

        self.feedman.feed_store.connect(
            'items-changed',
            self.on_feed_store_items_changed
        )

    @GObject.Property(type=Gtk.Widget, default=None, nick='main-widget')
    def main_widget(self) -> Optional[Gtk.Widget]:
        return self.__main_widget

    @main_widget.setter
    def main_widget(self, w: Gtk.Widget):
        self.__main_widget = w
        self.add_named(self.__main_widget, 'main_widget')

    def on_feed_store_items_changed(self, *args):
        if len(self.feedman.feed_store) == 0:
            self.set_visible_child(self.empty_state)
        else:
            self.set_visible_child(self.main_widget)

    def on_feeds_append(self, *args):
        self.set_visible_child(self.main_widget)
