from gi.repository import Gtk, Adw
from gfeeds.feeds_manager import FeedsManager
from gfeeds.confManager import ConfManager


@Gtk.Template(resource_path='/org/gabmus/gfeeds/ui/empty_state.ui')
class EmptyState(Adw.Bin):
    __gtype_name__ = 'EmptyState'

    def __init__(self):
        super().__init__()
        # done: hack workaround for:
        # https://gitlab.gnome.org/GNOME/libadwaita/-/issues/360
        # remove when fixed
        # self.get_child(
        # ).get_first_child().get_child().get_child().get_first_child(
        # ).set_tightening_threshold(0)
        # error inducing patch reverted, keeping it around if it comes back
        # in the future


class StackWithEmptyState(Gtk.Stack):
    def __init__(self, main_widget):
        super().__init__(
            vexpand=True, hexpand=True,
            transition_type=Gtk.StackTransitionType.CROSSFADE
        )
        self.feedman = FeedsManager()
        self.confman = ConfManager()
        self.main_widget = main_widget
        self.empty_state = EmptyState()
        self.add_named(self.main_widget, 'main_widget')
        self.add_named(self.empty_state, 'empty_state')
        self.set_visible_child(
            self.main_widget if len(self.confman.conf['feeds']) > 0
            else self.empty_state
        )

        self.feedman.feeds.connect(
            'pop',
            self.on_feeds_pop
        )
        self.feedman.connect(
            'feedmanager_refresh_end',
            self.on_feeds_pop
        )
        self.feedman.feeds.connect(
            'append',
            self.on_feeds_append
        )

    def on_feeds_pop(self, *args):
        if len(self.feedman.feeds) == 0:
            self.set_visible_child(self.empty_state)
        else:
            self.set_visible_child(self.main_widget)

    def on_feeds_append(self, *args):
        self.set_visible_child(self.main_widget)
