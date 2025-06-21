from gi.repository import Gtk, Adw
from rilato.confManager import ConfManager
from rilato.feeds_manager import FeedsManager
from rilato.feeds_view import (
    FeedsViewAllListboxRow,
    FeedsViewListbox,
    FeedsViewTagListboxRow,
)
from rilato.tag_store import TagObj


@Gtk.Template(resource_path="/org/gabmus/rilato/ui/filter_view.ui")
class FilterView(Adw.Bin):
    __gtype_name__ = "FilterView"
    all_listbox = Gtk.Template.Child()
    tags_listbox = Gtk.Template.Child()
    feeds_listbox_bin = Gtk.Template.Child()

    def __init__(self):
        super().__init__()
        self.feedman = FeedsManager()
        self.confman = ConfManager()
        self.feeds_listbox = FeedsViewListbox(False)
        self.feeds_listbox.connect("row-activated", self.on_feeds_row_activated)
        self.feeds_listbox.connect("row-selected", self.on_feed_row_selected)
        self.feeds_listbox_bin.set_child(self.feeds_listbox)
        self.all_listbox_row = FeedsViewAllListboxRow()
        self.all_listbox.append(self.all_listbox_row)
        self.all_listbox.select_row(self.all_listbox_row)
        self.tags_listbox.bind_model(
            self.feedman.tag_store, self.__create_tag_row, None
        )

    def __create_tag_row(self, tag: TagObj, *args) -> FeedsViewTagListboxRow:
        row = FeedsViewTagListboxRow(tag)
        return row

    @Gtk.Template.Callback()
    def on_all_row_activated(self, *_):
        for lb in (self.tags_listbox, self.feeds_listbox):
            lb.select_row(None)
        self.confman.emit("rilato_filter_changed", None)

    @Gtk.Template.Callback()
    def on_tags_row_activated(self, _, row):
        for lb in (self.all_listbox, self.feeds_listbox):
            lb.select_row(None)
        self.confman.emit("rilato_filter_changed", [row.title])

    def on_feeds_row_activated(self, _, row):
        for lb in (self.all_listbox, self.tags_listbox):
            lb.select_row(None)
        self.confman.emit("rilato_filter_changed", row.feed)

    def on_feed_row_selected(self, _, row):
        if not row and not self.tags_listbox.get_selected_row():
            self.all_listbox.select_row(self.all_listbox_row)
