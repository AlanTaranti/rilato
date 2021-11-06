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
from gfeeds.scrolled_message_dialog import ScrolledMessageDialog
from gfeeds.get_children import get_children
from functools import reduce
from operator import or_


class ManageTagsListboxRow(Gtk.ListBoxRow):
    __gsignals__ = {
        'tag_deleted': (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (str,)  # tag deleted
        ),
    }

    def __init__(self, tag, active=True, **kwargs):
        super().__init__(**kwargs)
        self.builder = Gtk.Builder.new_from_resource(
            '/org/gabmus/gfeeds/ui/manage_tags_listbox_row_content.ui'
        )
        self.tag = tag
        self.main_box = self.builder.get_object('main_box')
        self.label = self.builder.get_object('label')
        self.checkbox = self.builder.get_object('checkbox')
        self.delete_btn = self.builder.get_object('delete_btn')
        self.checkbox.set_active(active)
        self.label.set_text(self.tag)

        self.checkbox_handler_id = self.checkbox.connect(
            'toggled',
            self.on_checkbox_toggled
        )

        self.delete_btn.connect(
            'clicked',
            lambda *args: self.emit('tag_deleted', self.tag)
        )

        self.set_child(self.main_box)

    def on_checkbox_toggled(self, checkbox):
        with checkbox.handler_block(self.checkbox_handler_id):
            checkbox.set_inconsistent(False)
            checkbox.set_active(not checkbox.get_active())
        self.emit('activate')


class ManageTagsContent(Adw.Bin):
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

    def __init__(self, flap, window, **kwargs):
        super().__init__(width_request=280, **kwargs)
        self.get_style_context().add_class('background')
        self.builder = Gtk.Builder.new_from_resource(
            '/org/gabmus/gfeeds/ui/manage_tags_content.ui'
        )
        self.confman = ConfManager()
        self.flap = flap
        self.window = window
        self.main_box = self.builder.get_object('main_box')
        self.add_tag_btn = self.builder.get_object('add_tag_btn')
        self.tags_entry = self.builder.get_object('tags_entry')
        self.tags_listbox = self.builder.get_object('tags_listbox')

        self.tags_listbox.connect(
            'row-activated',
            self.on_tags_listbox_row_activated
        )

        self.tags_listbox.set_sort_func(
            self.tags_listbox_sorting_func,
            None,
            False
        )

        self.tags_entry.connect('changed', self.on_tags_entry_changed)
        self.tags_entry.connect(
            'activate',
            lambda *args: self.on_add_new_tag(
                self.tags_entry.get_text().strip()
            )
        )
        self.add_tag_btn.connect(
            'clicked',
            lambda *args: self.on_add_new_tag(
                self.tags_entry.get_text().strip()
            )
        )

        self.set_child(self.main_box)
        self.populate_listbox()

    def tags_listbox_sorting_func(self, row1, row2, data, notify_destroy):
        return row1.tag.lower() > row2.tag.lower()

    def populate_listbox(self):
        for row in get_children(self.tags_listbox):
            self.tags_listbox.remove(row)
        for tag in self.confman.conf['tags']:
            self.tags_listbox_add_row(tag, False)
        self.tags_listbox.show()

    def on_tags_listbox_row_activated(self, listbox, row):
        with row.checkbox.handler_block(row.checkbox_handler_id):
            row.checkbox.set_inconsistent(False)
            row.checkbox.set_active(not row.checkbox.get_active())
        if row.checkbox.get_active():
            self.on_add_new_tag(row.tag)
        else:
            self.emit('tag_removed', row.tag)

    def tags_listbox_add_row(self, tag: str, show_all=True):
        n_row = ManageTagsListboxRow(tag)
        self.tags_listbox.append(n_row)
        n_row.connect('tag_deleted', self.on_tag_deleted)

    def tags_listbox_get_row_by_tag(self, tag):
        for row in get_children(self.tags_listbox):
            if row.tag == tag:
                return row
        return None

    def on_add_new_tag(self, n_tag):
        if n_tag == '':
            return
        self.tags_entry.set_text('')
        self.emit('new_tag_added', n_tag)
        rows = get_children(self.tags_listbox)
        if len(rows) == 0 or not reduce(or_, [
                row.tag.lower() == n_tag.lower()
                for row in rows
        ]):
            self.tags_listbox_add_row(n_tag)

    def on_tags_entry_changed(self, *args):
        self.add_tag_btn.set_sensitive(
            self.tags_entry.get_text().strip() != ''
        )

    def on_tag_deleted(self, caller, tag):
        self.tags_listbox.remove(caller)
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


class ManageFeedsHeaderbar(Gtk.HeaderBar):
    def __init__(self, flap, **kwargs):
        super().__init__(
            title_widget=Adw.WindowTitle(title=_('Manage Feeds')),
            show_title_buttons=True,
            **kwargs
        )
        self.confman = ConfManager()
        self.flap=flap

        self.select_all_btn = Gtk.Button.new_from_icon_name(
            'edit-select-all-symbolic'
        )
        self.select_all_btn.set_tooltip_text(_('Select/Unselect all'))

        self.delete_btn = Gtk.Button(
            icon_name='user-trash-symbolic',
            tooltip_text=_('Delete selected feeds')
        )
        self.delete_btn.get_style_context().add_class('destructive-action')

        self.tags_btn = Gtk.ToggleButton(icon_name='tag-symbolic')
        self.tags_btn.set_tooltip_text(_('Manage tags for selected feeds'))

        self.pack_end(self.delete_btn)
        self.pack_start(self.tags_btn)
        self.pack_start(self.select_all_btn)

        self.set_actions_sensitive(False)

    def set_actions_sensitive(self, state):
        for w in (self.delete_btn, self.tags_btn):
            w.set_sensitive(state)
        self.flap.set_swipe_to_open(state)


class ManageFeedsListboxRow(FeedsViewListboxRow):
    def __init__(self, feed, **kwargs):
        super().__init__(feed, **kwargs)
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
            selection_mode=Gtk.SelectionMode.NONE
        )

    def add_feed(self, feed):
        self.append(ManageFeedsListboxRow(feed))

    def on_row_activated(self, listbox, row):
        with row.checkbox.handler_block(row.checkbox_handler_id):
            row.checkbox.set_active(not row.checkbox.get_active())


class ManageFeedsScrolledWindow(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__(
            vexpand=True,
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            vscrollbar_policy=Gtk.PolicyType.AUTOMATIC
        )
        self.listbox = ManageFeedsListbox()
        self.set_size_request(360, 500)
        self.set_child(self.listbox)


class DeleteFeedsConfirmMessageDialog(ScrolledMessageDialog):
    def __init__(self, parent, selected_feeds):
        super().__init__(
            transient_for=parent,
            modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=_('Do you want to delete these feeds?')
        )

        self.format_secondary_markup(
            '\n'.join([escape(f.title) for f in selected_feeds])
        )


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
        self.tags_flap.connect(
            'tag_deleted',
            self.on_tag_deleted
        )

    def on_new_tag_added(self, caller, tag):
        self.confman.add_tag(
            tag,
            [feed.rss_link for feed in self.get_selected_feeds()]
        )

    def on_tag_removed(self, caller, tag):
        self.confman.remove_tag(
            tag,
            [feed.rss_link for feed in self.get_selected_feeds()]
        )

    def on_tag_deleted(self, caller, tag):
        self.confman.delete_tag(tag)

    def get_selected_feeds(self):
        return [
            row.feed
            for row in get_children(self.listbox)
            if row.checkbox.get_active()
        ]

    def on_delete_clicked(self, *args):
        selected_feeds = self.get_selected_feeds()
        dialog = DeleteFeedsConfirmMessageDialog(self, selected_feeds)

        def on_response(_dialog, res):
            _dialog.close()
            if res == Gtk.ResponseType.YES:
                self.feedman.delete_feeds(selected_feeds)
                self.headerbar.set_actions_sensitive(False)

        dialog.connect('response', on_response)
        dialog.present()

    def on_select_all_clicked(self, *args):
        unselect = True
        for row in get_children(self.listbox):
            if not row.checkbox.get_active():
                unselect = False
                row.emit('activate')
        if unselect:
            for row in get_children(self.listbox):
                row.emit('activate')

    def on_row_activated(self, listbox, activated_row):
        for row in get_children(listbox):
            if row.checkbox.get_active():
                self.headerbar.set_actions_sensitive(True)
                return
        self.headerbar.set_actions_sensitive(False)
