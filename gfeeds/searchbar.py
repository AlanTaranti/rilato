from gi.repository import Gtk, Handy


class GFeedsSearchbar(Gtk.SearchBar):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_hexpand(False)
        self.entry = Gtk.Entry()
        self.entry.set_icon_from_icon_name(
            Gtk.EntryIconPosition.PRIMARY,
            'system-search-symbolic'
        )
        self.set_child(self.entry)
        self.set_show_close_button(False)
        self.set_search_mode(False)
        self.connect_entry(self.entry)
        self.show_all()
        # self.set_size_request(360, -1)
