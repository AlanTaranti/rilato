from math import ceil
from os.path import isfile
from gfeeds.feed_item import FeedItem
from gfeeds.util.sha import shasum
from gfeeds.util.download_manager import download_raw
from gi.repository import Gtk, GLib, Pango
from gfeeds.confManager import ConfManager
from gfeeds.simple_avatar import SimpleAvatar
from gfeeds.util.relative_day_formatter import humanize_datetime
from gfeeds.sidebar_row_popover import RowPopover
from gfeeds.accel_manager import add_mouse_button_accel, add_longpress_accel
from bs4 import BeautifulSoup


@Gtk.Template(resource_path='/org/gabmus/gfeeds/ui/sidebar_listbox_row.ui')
class SidebarRow(Gtk.Box):
    __gtype_name__ = 'SidebarRow'
    title_label = Gtk.Template.Child()
    origin_label = Gtk.Template.Child()
    icon_container = Gtk.Template.Child()
    date_label = Gtk.Template.Child()
    picture_view_container = Gtk.Template.Child()

    def __init__(self, fetch_image_thread_pool):
        super().__init__()
        self.fetch_image_thread_pool = fetch_image_thread_pool
        self.feed_item = None
        self.signal_ids = list()
        self.confman = ConfManager()

        self.confman.connect(
            'gfeeds_full_article_title_changed',
            self.on_full_article_title_changed
        )
        self.on_full_article_title_changed()
        self.confman.connect(
            'gfeeds_full_feed_name_changed',
            self.on_full_feed_name_changed
        )
        self.on_full_feed_name_changed()

        self.icon = SimpleAvatar()
        self.icon_container.append(self.icon)

        self.datestr = ''
        self.picture_view = Gtk.Picture(overflow=Gtk.Overflow.HIDDEN)
        self.picture_view.get_style_context().add_class('card')
        self.picture_view_container.append(self.picture_view)
        # picture_view_container is visible=False on init

        self.confman.connect('show_thumbnails_changed', self.set_article_image)

        self.popover = RowPopover(self)

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

    def set_feed_item(self, feed_item: FeedItem):
        if not feed_item or self.feed_item == feed_item:
            return
        if self.feed_item is not None:
            for sig_id in self.signal_ids:
                self.feed_item.disconnect(sig_id)
        self.signal_ids = list()

        self.feed_item = feed_item
        self.signal_ids.append(
            self.feed_item.connect(
                'notify::read', lambda *args: self.set_read()
            )
        )
        self.signal_ids.append(
            self.feed_item.connect('changed', self.on_feed_item_changed)
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
        self.set_read()
        self.on_feed_item_changed()

    def on_feed_item_changed(self, *args):
        if self.feed_item is None:
            return
        self.datestr = humanize_datetime(self.feed_item.pub_date)
        self.date_label.set_text(self.datestr)

    def set_article_image(self, *args):
        if not self.confman.conf['show_thumbnails'] or self.feed_item is None:
            self.picture_view_container.set_visible(False)
            return

        def cb(img):
            if img is None:
                self.picture_view_container.set_visible(False)
            else:
                self.picture_view_container.set_visible(True)
                self.picture_view.set_filename(img)
                cw, ch = self.picture_view.get_paintable(
                ).compute_concrete_size(270, 0, 1200, 1200)
                self.picture_view.set_size_request(-1, ceil(ch))
                self.picture_view_container.set_visible(True)

        def af():
            if self.feed_item is None:
                return
            dest = None
            if (
                    self.feed_item.identifier in
                    self.confman.article_thumb_cache.keys()
            ):
                dest = self.confman.article_thumb_cache[
                    self.feed_item.identifier
                ]
                if not isfile(dest):
                    download_raw(self.feed_item.image_url, dest)
                GLib.idle_add(cb, dest if dest and isfile(dest) else None)
                return
            else:
                try:
                    img_url = self.feed_item.image_url
                    if not img_url:
                        img_url = self.feed_item.set_thumb_from_link()
                    if not img_url:
                        raise Exception()
                    ext = img_url.split('.')[-1].lower().strip()
                    if '?' in ext:
                        ext = ext.split('?')[0]
                    if ext not in ('png', 'jpg', 'gif', 'svg'):
                        raise Exception()
                    dest = str(self.confman.thumbs_cache_path.joinpath(
                        shasum(img_url) + '.' + ext
                    ))
                    if not isfile(dest):
                        download_raw(img_url, dest)
                    self.confman.article_thumb_cache[
                        self.feed_item.identifier
                    ] = dest
                    self.confman.save_article_thumb_cache()
                except Exception:
                    pass
            if dest and isfile(dest):
                GLib.idle_add(cb, dest)
                return
            else:
                self.confman.article_thumb_cache[
                    self.feed_item.identifier
                ] = ''
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
            self.feed_item.read = read
        if self.feed_item.read:
            self.set_dim(True)
        else:
            self.set_dim(False)
        self.popover.on_feed_item_set()

    def set_dim(self, state):
        for w in (
                self.title_label,
                self.icon
        ):
            if state:
                w.get_style_context().add_class('dim-label')
            else:
                w.get_style_context().remove_class('dim-label')
