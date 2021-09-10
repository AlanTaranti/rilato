from gi.repository import Gtk


class ScrolledMessageDialog(Gtk.MessageDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.builder = Gtk.Builder.new_from_resource(
            '/org/gabmus/gfeeds/ui/scrolled_label.ui'
        )
        self.scrolled_win = self.builder.get_object('scrolled_win')
        self.label = self.builder.get_object('label')

        self.get_content_area().pack_start(self.scrolled_win, True, True, 0)
        self.get_content_area().set_spacing(0)
        self.get_message_area().set_spacing(0)
        self.title_label = self.get_message_area().get_children()[0]
        self.secondary_label = self.get_message_area().get_children()[1]
        self.title_label.set_margin_bottom(20)
        # Hiding default secondary text, because I need it set to make the
        # title pretty but I use a custom widget for the secondary text
        self.secondary_label.set_visible(False)
        self.secondary_label.set_no_show_all(True)

    def format_secondary_markup(self, message):
        super().format_secondary_markup(' ')
        self.label.set_markup(message)
