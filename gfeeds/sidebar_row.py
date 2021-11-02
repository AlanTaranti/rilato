from threading import Thread
from gfeeds.picture_view import PictureView
from os.path import isfile
from gfeeds.sha import shasum
from gfeeds.download_manager import download_raw
from gi.repository import Gtk, GLib, Pango, Adw
from gfeeds.confManager import ConfManager
from gfeeds.simple_avatar import SimpleAvatar
from gfeeds.relative_day_formatter import get_date_format
from gfeeds.sidebar_row_popover import RowPopover


class SidebarRow(Adw.Bin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.get_style_context().add_class('activatable')
        self.feed_item_wrapper = None
        self.feed_item_changed_signal_id = None
        self.feed_item = None
        self.confman = ConfManager()

        self.builder = Gtk.Builder.new_from_resource(
            '/org/gabmus/gfeeds/ui/sidebar_listbox_row.ui'
        )
        self.container_box = self.builder.get_object('container_box')
        self.title_label = self.builder.get_object('title_label')
        self.confman.connect(
            'gfeeds_full_article_title_changed',
            self.on_full_article_title_changed
        )
        self.on_full_article_title_changed()
        self.origin_label = self.builder.get_object('origin_label')
        self.confman.connect(
            'gfeeds_full_feed_name_changed',
            self.on_full_feed_name_changed
        )
        self.on_full_feed_name_changed()

        self.icon_container = self.builder.get_object('icon_container')
        self.icon = SimpleAvatar()
        self.icon_container.append(self.icon)

        # Date & time stuff is long
        self.date_label = self.builder.get_object('date_label')
        self.datestr = ''

        self.picture_view_container = self.builder.get_object(
            'picture_view_container'
        )
        self.picture_view = None
        self.confman.connect('show_thumbnails_changed', self.set_article_image)

        self.popover = RowPopover(self)

        self.set_child(self.container_box)

    def set_feed_item(self, feed_item_wrapper, just_refresh=False):
        if not feed_item_wrapper:
            return

        if (
                self.feed_item_changed_signal_id is not None and
                self.feed_item_wrapper is not None and
                not just_refresh
        ):
            self.feed_item_wrapper.disconnect(self.feed_item_changed_signal_id)
            self.feed_item_changed_signal_id = None

        if not just_refresh:
            self.feed_item_wrapper = feed_item_wrapper
            self.feed_item = feed_item_wrapper.feed_item
            self.feed_item_changed_signal_id = self.feed_item_wrapper.connect(
                'changed', lambda *args: self.set_feed_item(
                    self.feed_item_wrapper, True
                )
            )

        self.origin_label.set_text(self.feed_item.parent_feed.title)
        self.title_label.set_text(self.feed_item.title)
        tz_sec_offset = self.feed_item.pub_date.utcoffset().total_seconds()
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
            self.feed_item.pub_date.year,
            self.feed_item.pub_date.month,
            self.feed_item.pub_date.day,
            self.feed_item.pub_date.hour,
            self.feed_item.pub_date.minute,
            self.feed_item.pub_date.second
        ).to_local().format(get_date_format(self.feed_item.pub_date))
        self.date_label.set_text(
            self.datestr
        )
        self.icon.set_image(
            self.feed_item.parent_feed.title,
            self.feed_item.parent_feed.favicon_path
        )
        self.set_article_image()
        self.set_read()
        self.popover.on_feed_item_set()

    def set_article_image(self, *args):
        if self.picture_view is not None:
            self.picture_view_container.remove(self.picture_view)
            del self.picture_view
            self.picture_view = None
        if not self.confman.conf['show_thumbnails'] or self.feed_item is None:
            return

        def af():
            dest = None
            if self.feed_item.link in self.confman.article_thumb_cache.keys():
                dest = self.confman.article_thumb_cache[self.feed_item.link]
            else:
                try:
                    if self.feed_item.image_url is None:
                        self.feedi_tem.set_thumb_from_link()
                    if self.feed_item.image_url is None:
                        return
                    ext = \
                        self.feed_item.image_url.split('.')[-1].lower().strip()
                    if ext not in ('png', 'jpg', 'gif', 'svg'):
                        return
                    dest = (
                        self.confman.thumbs_cache_path + '/' +
                        shasum(self.feed_item.image_url) + '.' + ext
                    )
                    if not isfile(dest):
                        download_raw(self.feed_item.image_url, dest)
                    self.confman.article_thumb_cache[self.feed_item.link] = dest
                except Exception:
                    return
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
        if self.feed_item is None:
            return
        if read is not None:
            self.feed_item.set_read(read)
        if self.feed_item.read:
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
