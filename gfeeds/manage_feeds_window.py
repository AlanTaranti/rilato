from gettext import gettext as _
from gfeeds.accel_manager import add_accelerators
from gi.repository import Gtk, GObject, Adw
from xml.sax.saxutils import escape
from gfeeds.confManager import ConfManager
from gfeeds.feeds_manager import FeedsManager
from gfeeds.feeds_view import (
    FeedsViewListbox,
    FeedsViewListboxRow
)
from gfeeds.scrolled_dialog import ScrolledDialog
from gfeeds.get_children import get_children
from gfeeds.tag_store import TagObj


@Gtk.Template(resource_path='/org/gabmus/gfeeds/ui/manage_tags_listbox_row.ui')
class ManageTagsListboxRow(Gtk.ListBoxRow):
    __gtype_name__ = 'ManageTagsListboxRow'
    label = Gtk.Template.Child()
    checkbox = Gtk.Template.Child()
    delete_btn = Gtk.Template.Child()

    __gsignals__ = {
        'tag_deleted': (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (str,)  # tag deleted
        ),
    }

    def __init__(self, tag, active=True):
        super().__init__()
        self.tag = tag
        self.checkbox.set_active(active)
        self.label.set_text(self.tag)

        self.checkbox_handler_id = self.checkbox.connect(
            'toggled',
            self.on_checkbox_toggled
        )

    @Gtk.Template.Callback()
    def on_delete_btn_clicked(self, *args):
        self.emit('tag_deleted', self.tag)

    def on_checkbox_toggled(self, checkbox):
        with checkbox.handler_block(self.checkbox_handler_id):
            checkbox.set_inconsistent(False)
            checkbox.set_active(not checkbox.get_active())
        self.emit('activate')


@Gtk.Template(resource_path='/org/gabmus/gfeeds/ui/manage_tags_content.ui')
class ManageTagsContent(Adw.Bin):
    __gtype_name__ = 'ManageTagsContent'
    add_tag_btn = Gtk.Template.Child()
    tags_entry = Gtk.Template.Child()
    tags_listbox = Gtk.Template.Child()

    __gsignals__ = {
        'new_tag_added': (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (str,)  # tag added
        ),
        # removed or deleted?
        # removed: removed from selected feeds
        # deleted: deleted from the whole app
        'tag_removed': (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (str,)  # tag removed
        ),
        'tag_deleted': (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (str,)  # tag deleted
        ),
    }

    def __init__(self, flap, window):
        super().__init__()
        self.confman = ConfManager()
        self.feedman = FeedsManager()
        self.flap = flap
        self.window = window
        self.tags_listbox.bind_model(
            self.feedman.tag_store.sort_store, self.__create_tag_row, None
        )

    @Gtk.Template.Callback()
    def on_submit_add_tag(self, *_):
        n_tag = self.tags_entry.get_text().strip()
        if not n_tag:
            return
        self.emit('new_tag_added', n_tag)
        self.tags_entry.set_text('')

    def __create_tag_row(self, tag: TagObj, *_) -> ManageTagsListboxRow:
        row = ManageTagsListboxRow(tag.name, True)
        row.connect('tag_deleted', self.on_tag_deleted)
        return row

    @Gtk.Template.Callback()
    def on_tags_listbox_row_activated(self, _, row):
        with row.checkbox.handler_block(row.checkbox_handler_id):
            row.checkbox.set_inconsistent(False)
            row.checkbox.set_active(not row.checkbox.get_active())
        if row.checkbox.get_active():
            self.emit('new_tag_added', row.tag)
        else:
            self.emit('tag_removed', row.tag)

    def tags_listbox_get_row_by_tag(self, tag):
        for row in get_children(self.tags_listbox):
            if row.tag == tag:
                return row
        return None

    @Gtk.Template.Callback()
    def on_tags_entry_changed(self, *_):
        self.add_tag_btn.set_sensitive(
            self.tags_entry.get_text().strip() != ''
        )

    def on_tag_deleted(self, caller, tag):
        self.feedman.tag_store.remove_tag(tag)
        self.emit('tag_deleted', tag)

    def set_reveal(self, reveal: bool):
        if not reveal:
            return self.flap.set_reveal_flap(False)
        self.add_tag_btn.set_sensitive(False)
        self.tags_entry.set_text('')
        selected_feeds = [f.rss_link for f in self.window.get_selected_feeds()]
        for tag in self.confman.conf['tags']:
            all_have_tag = True
            some_have_tag = False
            for feed in selected_feeds:
                if (
                        'tags' in self.confman.conf['feeds'][feed].keys() and
                        tag in self.confman.conf['feeds'][feed]['tags']
                ):
                    some_have_tag = True
                else:
                    all_have_tag = False
            t_row = self.tags_listbox_get_row_by_tag(tag)
            if t_row is not None:
                with t_row.checkbox.handler_block(t_row.checkbox_handler_id):
                    t_row.checkbox.set_inconsistent(False)
                    if some_have_tag and not all_have_tag:
                        t_row.checkbox.set_inconsistent(True)
                    elif all_have_tag:
                        t_row.checkbox.set_active(True)
                    else:
                        t_row.checkbox.set_active(False)
        self.flap.set_reveal_flap(True)


@Gtk.Template(resource_path='/org/gabmus/gfeeds/ui/manage_feeds_headerbar.ui')
class ManageFeedsHeaderbar(Gtk.HeaderBar):
    __gtype_name__ = 'ManageFeedsHeaderbar'
    tags_btn = Gtk.Template.Child()
    select_all_btn = Gtk.Template.Child()
    delete_btn = Gtk.Template.Child()

    def __init__(self, flap):
        super().__init__()
        self.confman = ConfManager()
        self.flap = flap

    def set_actions_sensitive(self, state):
        for w in (self.delete_btn, self.tags_btn):
            w.set_sensitive(state)
        self.flap.set_swipe_to_open(state)


class ManageFeedsListboxRow(FeedsViewListboxRow):
    def __init__(self, feed, **kwargs):
        super().__init__(feed, count=False, **kwargs)
        self.checkbox.set_visible(True)
        self.checkbox_handler_id = self.checkbox.connect(
            'toggled',
            self.on_checkbox_toggled
        )

    def on_checkbox_toggled(self, checkbox):
        with checkbox.handler_block(self.checkbox_handler_id):
            checkbox.set_active(not checkbox.get_active())
        self.emit('activate')


class ManageFeedsListbox(FeedsViewListbox):
    def __init__(self):
        super().__init__(
            selection_mode=Gtk.SelectionMode.NONE,
            row_class=ManageFeedsListboxRow,
            do_filter=False
        )
        self.connect('row-activated', self.on_row_activated)

    def on_row_activated(self, _, row):
        with row.checkbox.handler_block(row.checkbox_handler_id):
            row.checkbox.set_active(not row.checkbox.get_active())


class ManageFeedsScrolledWindow(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__(
            vexpand=True,
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
            width_request=360, height_request=500
        )
        self.listbox = ManageFeedsListbox()
        self.set_child(self.listbox)


class GFeedsManageFeedsWindow(Adw.Window):
    def __init__(self, appwindow, **kwargs):
        super().__init__(
            modal=True,
            transient_for=appwindow,
            **kwargs
        )
        self.appwindow = appwindow
        self.confman = ConfManager()
        self.feedman = FeedsManager()
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.scrolled_window = ManageFeedsScrolledWindow()
        self.listbox = self.scrolled_window.listbox
        self.flap = Adw.Flap(
            flap_position=Gtk.PackType.START,
            fold_policy=Adw.FlapFoldPolicy.ALWAYS,
            modal=True,
            reveal_flap=False,
            swipe_to_open=True, swipe_to_close=True
        )
        self.tags_flap = ManageTagsContent(self.flap, self)
        self.flap.set_content(self.scrolled_window)
        self.flap.set_flap(self.tags_flap)
        self.headerbar = ManageFeedsHeaderbar(self.flap)
        self.headerbar.tags_btn.connect(
            'toggled', lambda btn:
                self.tags_flap.set_reveal(btn.get_active())
        )
        self.flap.connect(
            'notify::reveal-flap', lambda *args:
                self.headerbar.tags_btn.set_active(
                    self.flap.get_reveal_flap()
                )
        )

        self.headerbar.delete_btn.connect(
            'clicked',
            self.on_delete_clicked
        )
        self.headerbar.select_all_btn.connect(
            'clicked',
            self.on_select_all_clicked
        )
        self.listbox.connect('row-activated', self.on_row_activated)
        self.set_title(_('Manage Feeds'))

        self.window_handle = Gtk.WindowHandle()
        self.window_handle.set_child(self.headerbar)
        self.main_box.append(self.window_handle)
        self.window_handle.set_vexpand(False)

        self.main_box.append(self.flap)
        self.set_content(self.main_box)

        add_accelerators(
            self,
            [{
                'combo': 'Escape',
                'cb': lambda *args: self.close()
            }]
        )

        self.tags_flap.connect(
            'new_tag_added',
            self.on_new_tag_added
        )
        self.tags_flap.connect(
            'tag_removed',
            self.on_tag_removed
        )

    def on_new_tag_added(self, _, tag):
        self.feedman.tag_store.add_tag(
            tag,
            self.get_selected_feeds()
        )
        # TODO if tag is currently selected invalidate filter

    def on_tag_removed(self, _, tag_name):
        self.confman.remove_tag(
            tag_name,
            [feed.rss_link for feed in self.get_selected_feeds()]
        )
        # TODO if tag is currently selected invalidate filter
        tag = self.feedman.tag_store.get_tag(tag_name)
        if tag is not None:
            for feed in self.get_selected_feeds():
                if tag in feed.tags:
                    feed.tags.remove(tag)
                    tag.unread_count -= feed.unread_count

    def get_selected_feeds(self):
        return [
            row.feed
            for row in get_children(self.listbox)
            if row.checkbox.get_active()
        ]

    def on_delete_clicked(self, *__):
        selected_feeds = self.get_selected_feeds()
        dialog = ScrolledDialog(
            transient_for=self,
            title=_('Do you want to delete these feeds?'),
            message='\n'.join([escape(f.title) for f in selected_feeds])
        )

        def on_response(_dialog, res):
            _dialog.close()
            if res == Gtk.ResponseType.YES:
                self.feedman.delete_feeds(selected_feeds)
                self.headerbar.set_actions_sensitive(False)

        dialog.connect('response', on_response)
        dialog.present()

    def on_select_all_clicked(self, *_):
        unselect = True
        for row in get_children(self.listbox):
            if not row.checkbox.get_active():
                unselect = False
                row.emit('activate')
        if unselect:
            for row in get_children(self.listbox):
                row.emit('activate')

    def on_row_activated(self, listbox, _):
        for row in get_children(listbox):
            if row.checkbox.get_active():
                self.headerbar.set_actions_sensitive(True)
                return
        self.headerbar.set_actions_sensitive(False)
