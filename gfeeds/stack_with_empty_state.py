from gi.repository import Gtk
from gfeeds.feeds_manager import FeedsManager
from gfeeds.confManager import ConfManager


class StackWithEmptyState(Gtk.Stack):
    def __init__(self, main_widget):
        super().__init__(vexpand=True, hexpand=True)
        self.feedman = FeedsManager()
        self.confman = ConfManager()
        self.main_widget = main_widget
        self.empty_state = Gtk.Builder.new_from_resource(
            '/org/gabmus/gfeeds/ui/empty_state.ui'
        ).get_object('empty_state_box')
        self.empty_state.get_style_context().add_class(
            'navigation-sidebar'
        )
        self.main_widget.show()
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

        self.set_transition_type(
            Gtk.StackTransitionType.CROSSFADE
        )

        # self.set_size_request(360, 100)

    def on_feeds_pop(self, *args):
        if len(self.feedman.feeds) == 0:
            self.set_visible_child(self.empty_state)
        else:
            self.set_visible_child(self.main_widget)

    def on_feeds_append(self, *args):
        self.set_visible_child(self.main_widget)
