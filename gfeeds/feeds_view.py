from gettext import gettext as _
from gi.repository import GObject, Gtk, Pango
from gfeeds.confManager import ConfManager
from gfeeds.feeds_manager import FeedsManager
from gfeeds.feed import Feed
from gfeeds.simple_avatar import SimpleAvatar


class FeedsViewAllListboxRow(Gtk.ListBoxRow):
    def __init__(self):
        super().__init__()
        self.label = Gtk.Label(
            label='<b>' + _('All feeds') + '</b>',
            use_markup=True,
            margin_top=12, margin_bottom=12
        )
        self.set_child(self.label)


class FeedsViewListboxRow(Gtk.ListBoxRow):
    def __init__(self, feed, description=True, count=True):
        super().__init__()
        self.confman = ConfManager()
        self.feed = feed
        self.title = feed.title
        self.builder = Gtk.Builder.new_from_resource(
            '/org/gabmus/gfeeds/ui/manage_feeds_listbox_row.ui'
        )
        self.hbox = self.builder.get_object('hbox')
        self.checkbox = self.builder.get_object('check')
        self.checkbox.set_visible(False)

        self.icon_container = self.builder.get_object('icon_container')
        self.icon = SimpleAvatar()
        self.icon.set_image(
            self.feed.title,
            self.feed.favicon_path
        )
        self.icon_container.append(self.icon)

        self.name_label = self.builder.get_object('title_label')
        self.name_label.set_text(self.feed.title)
        self.confman.connect(
            'gfeeds_full_feed_name_changed',
            self.on_full_feed_name_changed
        )
        self.desc_label = self.builder.get_object('description_label')
        self.desc_label.set_visible(description)
        if description:
            self.desc_label.set_text(self.feed.description)
        else:
            self.name_label.set_ellipsize(Pango.EllipsizeMode.END)

        count_box = self.builder.get_object('count_box')
        self.count_label = self.builder.get_object('count_label')
        if count:
            if self.feed.unread_count == 0:
                self.count_label.set_visible(False)
            else:
                self.count_label.set_text(str(self.feed.unread_count))

            def transform_to(binding, value, user_data=None):
                return value > 0

            self.feed.bind_property(
                'unread-count', self.count_label,
                'visible', GObject.BindingFlags.DEFAULT,
                None, transform_to
            )
            self.feed.bind_property(
                'unread-count', self.count_label,
                'label', GObject.BindingFlags.DEFAULT
            )
        else:
            count_box.set_visible(False)

        self.set_child(self.hbox)
        self.on_full_feed_name_changed()

    def on_full_feed_name_changed(self, *args):
        self.name_label.set_ellipsize(
            Pango.EllipsizeMode.NONE if self.confman.conf['full_feed_name']
            else Pango.EllipsizeMode.END
        )

    def __repr__(self):
        return f'<FeedsViewListboxRow - {self.title}>'


class FeedsViewTagListboxRow(Gtk.ListBoxRow):
    def __init__(self, tag):
        super().__init__()
        self.tag = tag
        self.title = tag.name
        self.builder = Gtk.Builder.new_from_resource(
            '/org/gabmus/gfeeds/ui/manage_feeds_listbox_row.ui'
        )
        self.hbox = self.builder.get_object('hbox')
        self.checkbox = self.builder.get_object('check')
        self.checkbox.set_visible(False)
        self.icon_container = self.builder.get_object('icon_container')
        self.icon = Gtk.Image.new_from_icon_name('tag-symbolic')
        self.icon.set_pixel_size(32)
        self.icon_container.append(self.icon)

        self.name_label = self.builder.get_object('title_label')
        self.name_label.set_text(tag.name)
        self.desc_label = self.builder.get_object('description_label')
        self.desc_label.set_visible(False)
        self.set_child(self.hbox)

        self.count_label = self.builder.get_object('count_label')
        if self.tag.unread_count > 0:
            self.count_label.set_text(str(self.tag.unread_count))
        else:
            self.count_label.set_visible(False)

        def transform_to(binding, value, user_data=None):
            return value > 0

        self.tag.bind_property(
            'unread-count', self.count_label,
            'visible', GObject.BindingFlags.DEFAULT,
            None, transform_to
        )
        self.tag.bind_property(
            'unread-count', self.count_label,
            'label', GObject.BindingFlags.DEFAULT
        )

    def __repr__(self):
        return f'<FeedsViewTagListboxRow - {self.title}>'


class FeedsViewListbox(Gtk.ListBox):
    __gtype_name__ = 'FeedsViewListbox'

    def __init__(
            self, description=True, selection_mode=Gtk.SelectionMode.SINGLE,
            row_class=FeedsViewListboxRow, do_filter=True
    ):
        super().__init__(selection_mode=selection_mode)
        self.get_style_context().add_class('navigation-sidebar')
        self.get_style_context().add_class('background')
        self.description = description
        self.feedman = FeedsManager()
        self.confman = ConfManager()

        self.row_class = row_class
        self.bind_model(
            self.feedman.feed_store
            if do_filter
            else self.feedman.feed_store.sort_store,
            self.__create_feed_row,
            None
        )

    def __create_feed_row(self, feed: Feed, *args) -> Gtk.ListBoxRow:
        row = self.row_class(feed, description=self.description)
        return row


class FeedsViewScrolledWindow(Gtk.ScrolledWindow):
    def __init__(self, description=True):
        super().__init__(
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
            hexpand=False, vexpand=True, width_request=250
        )
        self.listbox = FeedsViewListbox(description)
        self.all_row = FeedsViewAllListboxRow()
        # self.listbox.append(self.all_row)
        # self.listbox.select_row(self.all_row)
        # self.set_size_request(360, 500)
        self.set_child(self.listbox)
