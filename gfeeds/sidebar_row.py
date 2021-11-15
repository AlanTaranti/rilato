from gfeeds.picture_view import PictureView
from os.path import isfile
from gfeeds.sha import shasum
from gfeeds.download_manager import download_raw
from gi.repository import Gtk, GLib, Pango, Adw
from gfeeds.confManager import ConfManager
from gfeeds.simple_avatar import SimpleAvatar
from gfeeds.relative_day_formatter import humanize_datetime
from gfeeds.sidebar_row_popover import RowPopover
from gfeeds.accel_manager import add_mouse_button_accel, add_longpress_accel
from bs4 import BeautifulSoup


class SidebarRow(Adw.Bin):
    def __init__(self, fetch_image_thread_pool):
        super().__init__()
        # self.get_style_context().add_class('activatable')
        self.fetch_image_thread_pool = fetch_image_thread_pool
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
        # self.picture_view = Gtk.Picture(
        #     width_request=200, height_request=200, can_shrink=True
        # )
        self.picture_view = PictureView(None)
        self.picture_view_container.append(self.picture_view)
        self.picture_view_container.set_visible(False)

        self.confman.connect('show_thumbnails_changed', self.set_article_image)

        self.popover = RowPopover(self)

        self.set_child(self.container_box)

        # longpress & right click
        self.longpress = add_longpress_accel(
            self, lambda *args: self.popover.popup()
        )
        self.rightclick = add_mouse_button_accel(
            self,
            lambda gesture, *args:
                self.popover.popup()
                if gesture.get_current_button() == 3  # 3 is right click
                else None
        )

    def set_feed_item(self, feed_item_wrapper):
        if (
                not feed_item_wrapper or
                self.feed_item_wrapper == feed_item_wrapper
        ):
            return

        if (
                self.feed_item_changed_signal_id is not None and
                self.feed_item_wrapper is not None
        ):
            self.feed_item_wrapper.disconnect(self.feed_item_changed_signal_id)
            self.feed_item_changed_signal_id = None

        self.feed_item_wrapper = feed_item_wrapper
        self.feed_item = feed_item_wrapper.feed_item
        self.feed_item_changed_signal_id = self.feed_item_wrapper.connect(
            'changed', self.on_feed_item_changed
        )

        self.origin_label.set_text(self.feed_item.parent_feed.title)
        self.title_label.set_text(
            BeautifulSoup(self.feed_item.title).text
            if '</' in self.feed_item.title else self.feed_item.title
        )
        self.icon.set_image(
            self.feed_item.parent_feed.title,
            self.feed_item.parent_feed.favicon_path
        )
        self.set_article_image()
        self.on_feed_item_changed()

    def on_feed_item_changed(self, *args):
        if self.feed_item is None:
            return
        self.set_read()
        self.datestr = humanize_datetime(self.feed_item.pub_date)
        self.date_label.set_text(self.datestr)
        self.popover.on_feed_item_set()

    def set_article_image(self, *args):
        if not self.confman.conf['show_thumbnails'] or self.feed_item is None:
            self.picture_view_container.set_visible(False)
            return

        def cb(img):
            if img is None:
                self.picture_view_container.set_visible(False)
            else:
                self.picture_view_container.set_visible(True)
                self.picture_view.set_file(img)
                GLib.timeout_add(
                    100,
                    lambda *args:
                        self.picture_view_container.set_visible(True)
                )
                # self.picture_view.set_filename(img)

        def af():
            if self.feed_item is None:
                return
            dest = None
            if self.feed_item.link in self.confman.article_thumb_cache.keys():
                dest = self.confman.article_thumb_cache[self.feed_item.link]
                GLib.idle_add(cb, dest if dest and isfile(dest) else None)
                return
            else:
                try:
                    if not self.feed_item.image_url:
                        self.feed_item.set_thumb_from_link()
                    if not self.feed_item.image_url:
                        raise Exception()
                    ext = \
                        self.feed_item.image_url.split('.')[-1].lower().strip()
                    if '?' in ext:
                        ext = ext.split('?')[0]
                    if ext not in ('png', 'jpg', 'gif', 'svg'):
                        raise Exception()
                    dest = str(self.confman.thumbs_cache_path.joinpath(
                        shasum(self.feed_item.image_url) + '.' + ext
                    ))
                    if not isfile(dest):
                        download_raw(self.feed_item.image_url, dest)
                    self.confman.article_thumb_cache[
                        self.feed_item.link
                    ] = dest
                    self.confman.save_article_thumb_cache()
                except Exception:
                    pass
            if dest and isfile(dest):
                GLib.idle_add(cb, dest)
                return
            else:
                self.confman.article_thumb_cache[self.feed_item.link] = ''
                self.confman.save_article_thumb_cache()
            GLib.idle_add(cb, None)

        self.fetch_image_thread_pool.submit(af)

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
