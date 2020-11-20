from gi.repository import Gtk


class GFeedsViewModeMenu(Gtk.PopoverMenu):
    def __init__(self, relative_to, **kwargs):
        super().__init__(**kwargs)
        self.set_modal(True)
        self.set_relative_to(relative_to)
        relative_to.set_popover(self)
        relative_to.set_sensitive(False)
        self.builder = Gtk.Builder.new_from_resource(
            '/org/gabmus/gfeeds/ui/extra_popover_menu.glade'
        )
        self.add(self.builder.get_object(
            'menu_box'
        ))
