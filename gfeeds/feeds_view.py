from gettext import gettext as _
from gi.repository import Gtk, Pango
from gfeeds.confManager import ConfManager
from gfeeds.feeds_manager import FeedsManager
from gfeeds.simple_avatar import SimpleAvatar
from gfeeds.get_children import get_children


class FeedsViewAllListboxRow(Gtk.ListBoxRow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.IS_ALL = True
        self.IS_TAG = False
        self.feed = None
        self.label = Gtk.Label()
        self.label.set_markup(
            '<b>' +
            _('All feeds') +
            '</b>'
        )
        self.label.set_use_markup(True)
        self.label.set_margin_top(12)
        self.label.set_margin_bottom(12)
        self.set_child(self.label)


class FeedsViewListboxRow(Gtk.ListBoxRow):
    def __init__(self, feed, description=True, **kwargs):
        super().__init__(**kwargs)
        self.confman = ConfManager()
        self.IS_ALL = False
        self.IS_TAG = False
        self.feed = feed
        self.title = feed.title
        self.builder = Gtk.Builder.new_from_resource(
            '/org/gabmus/gfeeds/ui/manage_feeds_listbox_row.ui'
        )
        self.hbox = self.builder.get_object('hbox')
        self.checkbox = self.builder.get_object('check')
        self.checkbox.set_visible(False)
        self.checkbox.hide()

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
            self.desc_label.hide()
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
    def __init__(self, tag, **kwargs):
        super().__init__(**kwargs)
        self.IS_TAG = True
        self.IS_ALL = False
        self.tag = tag
        self.title = tag
        self.feed = None
        self.builder = Gtk.Builder.new_from_resource(
            '/org/gabmus/gfeeds/ui/manage_feeds_listbox_row.ui'
        )
        self.hbox = self.builder.get_object('hbox')
        self.checkbox = self.builder.get_object('check')
        self.checkbox.set_visible(False)
        self.checkbox.hide()
        self.icon_container = self.builder.get_object('icon_container')
        self.icon = Gtk.Image.new_from_icon_name(
            'tag-symbolic'
        )
        self.icon.set_pixel_size(32)
        self.icon_container.append(self.icon)

        self.name_label = self.builder.get_object('title_label')
        self.name_label.set_text(tag)
        self.desc_label = self.builder.get_object('description_label')
        self.desc_label.set_visible(False)
        self.desc_label.hide()
        self.set_child(self.hbox)

    def __repr__(self):
        return f'<FeedsViewTagListboxRow - {self.title}>'


class FeedsViewListbox(Gtk.ListBox):
    # here kwargs is actually being used
    def __init__(self, description=True, tags=False, **kwargs):
        super().__init__(**kwargs)
        self.get_style_context().add_class('navigation-sidebar')
        self.get_style_context().add_class('background')
        self.description = description
        self.feedman = FeedsManager()
        self.confman = ConfManager()

        self.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.connect('row-activated', self.on_row_activated)

        for feed in self.feedman.feeds:
            self.add_feed(feed)
        self.feedman.feeds.connect(
            'empty',
            self.empty
        )
        self.feedman.feeds.connect(
            'append',
            self.on_feeds_append
        )
        self.feedman.feeds.connect(
            'pop',
            self.on_feeds_pop
        )

        if tags:
            self.confman.connect(
                'gfeeds_tags_append',
                self.on_tags_append
            )
            self.confman.connect(
                'gfeeds_tags_pop',
                self.on_tags_pop
            )

            for tag in self.confman.conf['tags']:
                self.on_tags_append(None, tag)

        self.set_sort_func(self.gfeeds_sort_func, None, False)

    def on_feeds_pop(self, caller, feed):
        self.remove_feed(feed)

    def on_feeds_append(self, caller, feed):
        self.add_feed(feed)

    def on_tags_append(self, caller, tag):
        self.append(FeedsViewTagListboxRow(tag))

    def on_tags_pop(self, caller, tag):
        for row in get_children(self):
            if row.IS_TAG and row.tag == tag:
                self.remove(row)
                break

    def add_feed(self, feed):
        self.append(FeedsViewListboxRow(feed, self.description))

    def on_row_activated(self, listbox, row):
        if row.IS_ALL:
            self.confman.emit('gfeeds_filter_changed', None)
            return
        if row.IS_TAG:
            self.confman.emit('gfeeds_filter_changed', [row.tag])
            return
        self.confman.emit('gfeeds_filter_changed', row.feed)

    def remove_feed(self, feed):
        for row in get_children(self):
            if not hasattr(row, 'IS_ALL'):
                continue
            if not row.IS_ALL:
                if row.feed == feed:
                    self.remove(row)
                    break

    def empty(self, *args):
        for row in get_children(self):
            if row and not row.IS_ALL and not row.IS_TAG:
                self.remove(row)

    def row_all_activate(self, skip=False):
        if skip:
            return
        for row in get_children(self):
            if row.IS_ALL:
                row.activate()
                break

    def gfeeds_sort_func(self, row1, row2, data, notify_destroy):
        if row1.IS_ALL:
            return False
        if row2.IS_ALL:
            return True
        if row1.IS_TAG and not row2.IS_TAG:
            return False
        if row2.IS_TAG and not row1.IS_TAG:
            return True
        return row1.title.lower() > row2.title.lower()


class FeedsViewScrolledWindow(Gtk.ScrolledWindow):
    def __init__(self, description=True, tags=False):
        super().__init__(
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
            hexpand=False, vexpand=True
        )
        self.listbox = FeedsViewListbox(description, tags)
        self.all_row = FeedsViewAllListboxRow()
        self.listbox.append(self.all_row)
        self.listbox.select_row(self.all_row)
        # self.set_size_request(360, 500)
        self.set_child(self.listbox)
        self.set_size_request(250, -1)
        # self.get_style_context().add_class('frame')
