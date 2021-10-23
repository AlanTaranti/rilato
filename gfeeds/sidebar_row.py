from threading import Thread
from gfeeds.picture_view import PictureView
from os.path import isfile
from gfeeds.sha import shasum
from gfeeds.download_manager import download_raw
from gi.repository import Gtk, GLib, Pango
from gfeeds.confManager import ConfManager
from gfeeds.initials_icon import InitialsIcon
from gfeeds.relative_day_formatter import get_date_format
from gfeeds.sidebar_row_popover import RowPopover


class GFeedsSidebarRow(Gtk.ListBoxRow):
    def __init__(self, feeditem, is_saved=False, **kwargs):
        super().__init__(**kwargs)
        self.is_saved = is_saved
        self.get_style_context().add_class('activatable')
        self.feeditem = feeditem
        self.confman = ConfManager()

        self.builder = Gtk.Builder.new_from_resource(
            '/org/gabmus/gfeeds/ui/sidebar_listbox_row.ui'
        )
        self.container_box = self.builder.get_object('container_box')
        self.title_label = self.builder.get_object('title_label')
        self.title_label.set_text(self.feeditem.title)
        self.confman.connect(
            'gfeeds_full_article_title_changed',
            self.on_full_article_title_changed
        )
        self.on_full_article_title_changed()
        self.origin_label = self.builder.get_object('origin_label')
        self.origin_label.set_text(self.feeditem.parent_feed.title)
        self.confman.connect(
            'gfeeds_full_feed_name_changed',
            self.on_full_feed_name_changed
        )
        self.on_full_feed_name_changed()

        self.icon_container = self.builder.get_object('icon_container')
        self.icon = InitialsIcon(
            self.feeditem.parent_feed.title,
            self.feeditem.parent_feed.favicon_path
        )
        self.icon_container.append(self.icon)

        # Date & time stuff is long
        self.date_label = self.builder.get_object('date_label')
        tz_sec_offset = self.feeditem.pub_date.utcoffset().total_seconds()
        glibtz = GLib.TimeZone(
            (
                '{0}{1}:{2}'.format(
                    '+' if tz_sec_offset >= 0 else '',
                    format(int(tz_sec_offset/3600), '02'),
                    format(int(
                        (tz_sec_offset - (int(tz_sec_offset/3600)*3600))/60
                    ), '02'),
                )
            ) or '+00:00'
        )
        self.datestr = GLib.DateTime(
            glibtz,
            self.feeditem.pub_date.year,
            self.feeditem.pub_date.month,
            self.feeditem.pub_date.day,
            self.feeditem.pub_date.hour,
            self.feeditem.pub_date.minute,
            self.feeditem.pub_date.second
        ).to_local().format(get_date_format(self.feeditem.pub_date))
        self.date_label.set_text(
            self.datestr
        )

        self.picture_view_container = self.builder.get_object(
            'picture_view_container'
        )
        self.picture_view = None
        self.confman.connect('show_thumbnails_changed', self.set_article_image)
        self.set_article_image()

        self.popover = RowPopover(self)

        self.set_child(self.container_box)
        self.set_read()

    def set_article_image(self, *args):
        if not self.confman.conf['show_thumbnails']:
            if self.picture_view is not None:
                self.picture_view_container.remove(self.picture_view)
                del self.picture_view
                self.picture_view = None
            return

        def af():
            if self.feeditem.image_url is None:
                self.feeditem.set_thumb_from_link()
            if self.feeditem.image_url is None:
                return
            ext = self.feeditem.image_url.split('.')[-1].lower()
            if ext not in ('png', 'jpg', 'gif'):
                return
            dest = (
                self.confman.thumbs_cache_path + '/' +
                shasum(self.feeditem.image_url) + '.' + ext
            )
            if not isfile(dest):
                download_raw(self.feeditem.image_url, dest)
            if isfile(dest):
                GLib.idle_add(cb, dest)

        def cb(img):
            self.picture_view = PictureView(img)
            self.picture_view_container.append(self.picture_view)

        Thread(target=af, daemon=True).start()

    def on_full_article_title_changed(self, *args):
        self.title_label.set_ellipsize(
            Pango.EllipsizeMode.NONE if self.confman.conf['full_article_title']
            else Pango.EllipsizeMode.END
        )

    def on_full_feed_name_changed(self, *args):
        self.origin_label.set_ellipsize(
            Pango.EllipsizeMode.NONE if self.confman.conf['full_feed_name']
            else Pango.EllipsizeMode.END
        )

    def set_read(self, read=None):
        if read is not None:
            self.feeditem.set_read(read)
        if self.feeditem.read:
            self.set_dim(True)
        else:
            self.set_dim(False)

    def set_dim(self, state):
        for w in (
                self.title_label,
                self.icon
        ):
            if state:
                w.get_style_context().add_class('dim-label')
            else:
                w.get_style_context().remove_class('dim-label')
