from gi.repository import Gtk
from .feeds_manager import FeedsManager

class StackWithEmptyState(Gtk.Stack):
    def __init__(self, main_widget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feedman = FeedsManager()
        self.main_widget = main_widget
        self.empty_state = Gtk.Builder.new_from_resource(
            '/org/gabmus/gfeeds/ui/empty_state.glade'
        ).get_object('empty_state_box')
        self.main_widget.show_all()
        self.add_named(self.main_widget, 'main_widget')
        self.add_named(self.empty_state, 'empty_state')
        self.set_visible_child(self.main_widget)

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
