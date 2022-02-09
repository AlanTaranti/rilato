from gettext import gettext as _
from gi.repository import Gtk, Pango
from gfeeds.confManager import ConfManager
from gfeeds.feeds_manager import FeedsManager
from gfeeds.rss_parser import Feed
from gfeeds.simple_avatar import SimpleAvatar
from gfeeds.get_children import get_children


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
    def __init__(self, feed, description=True):
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
        self.title = tag
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
        self.name_label.set_text(tag)
        self.desc_label = self.builder.get_object('description_label')
        self.desc_label.set_visible(False)
        self.set_child(self.hbox)

    def __repr__(self):
        return f'<FeedsViewTagListboxRow - {self.title}>'


class FeedsViewListbox(Gtk.ListBox):
    __gtype_name__ = 'FeedsViewListbox'

    def __init__(
            self, description=True, selection_mode=Gtk.SelectionMode.SINGLE,
            row_class=FeedsViewListboxRow
    ):
        super().__init__(selection_mode=selection_mode)
        self.get_style_context().add_class('navigation-sidebar')
        self.get_style_context().add_class('background')
        self.description = description
        self.feedman = FeedsManager()
        self.confman = ConfManager()

        self.row_class = row_class
        self.bind_model(self.feedman.feed_store, self.__create_feed_row, None)

#         if tags:
#             self.confman.connect(
#                 'gfeeds_tags_append',
#                 self.on_tags_append
#             )
#             self.confman.connect(
#                 'gfeeds_tags_pop',
#                 self.on_tags_pop
#             )
#
#             for tag in self.confman.conf['tags']:
#                 self.on_tags_append(None, tag)

#     def on_feeds_pop(self, caller, feed):
#         self.remove_feed(feed)
#
#     def on_feeds_append(self, caller, feed):
#         self.add_feed(feed)
#
#     def on_tags_append(self, caller, tag):
#         self.append(FeedsViewTagListboxRow(tag))
#
#     def on_tags_pop(self, caller, tag):
#         for row in get_children(self):
#             if row.IS_TAG and row.tag == tag:
#                 self.remove(row)
#                 break

    def __create_feed_row(self, feed: Feed, *args) -> Gtk.ListBoxRow:
        row = self.row_class(feed, description=self.description)
        return row

#     def remove_feed(self, feed):
#         for row in get_children(self):
#             if not hasattr(row, 'IS_ALL'):
#                 continue
#             if not row.IS_ALL:
#                 if row.feed == feed:
#                     self.remove(row)
#                     break
#
#     def empty(self, *args):
#         for row in get_children(self):
#             if row and not row.IS_ALL and not row.IS_TAG:
#                 self.remove(row)

    def row_all_activate(self, skip=False):
        if skip:
            return
        for row in get_children(self):
            if row.IS_ALL:
                row.activate()
                break

#     def gfeeds_sort_func(self, row1, row2, data, notify_destroy):
#         if row1.IS_ALL:
#             return False
#         if row2.IS_ALL:
#             return True
#         if row1.IS_TAG and not row2.IS_TAG:
#             return False
#         if row2.IS_TAG and not row1.IS_TAG:
#             return True
#         return row1.title.lower() > row2.title.lower()


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
