import sys
import argparse
from gettext import gettext as _
from os.path import isfile
from gi.repository import Gtk, Gio, GLib
from gfeeds.confManager import ConfManager
from gfeeds.feeds_manager import FeedsManager
from gfeeds.app_window import GFeedsAppWindow
from gfeeds.settings_window import show_settings_window
from gfeeds.opml_manager import (
    feeds_list_to_opml,
    add_feeds_from_opml
)
from gfeeds.opml_file_chooser import (
    GFeedsOpmlFileChooserDialog,
    GFeedsOpmlSavePathChooserDialog
)
from gfeeds.manage_feeds_window import GFeedsManageFeedsWindow
from gfeeds.confirm_add_dialog import GFeedsConfirmAddDialog
from gfeeds.shortcuts_window import show_shortcuts_window
from gfeeds.rss_link_from_file import get_feed_link_from_file
from gfeeds.get_children import get_children
from gfeeds.base_app import BaseApp, AppAction


class GFeedsApplication(BaseApp):
    def __init__(self):
        self.confman = ConfManager()
        super().__init__(
            app_id='org.gabmus.gfeeds',
            app_name='Feeds',
            app_actions=[
                AppAction(
                    name='show_read_items',
                    func=self.show_read_items,
                    accel='<Control>h',
                    stateful=True,
                    state_type=AppAction.StateType.BOOL,
                    state_default=self.confman.conf['show_read_items']
                ),
                AppAction(
                    name='view_mode_change',
                    func=self.view_mode_change,
                    stateful=True,
                    state_type=AppAction.StateType.RADIO,
                    state_default=self.confman.conf['default_view']
                ),
                AppAction(
                    name='set_all_read',
                    func=self.set_all_read
                ),
                AppAction(
                    name='set_all_unread',
                    func=self.set_all_unread
                ),
                AppAction(
                    name='manage_feeds',
                    func=self.manage_feeds
                ),
                AppAction(
                    name='import_opml',
                    func=self.import_opml
                ),
                AppAction(
                    name='export_opml',
                    func=self.export_opml
                ),
                AppAction(
                    name='settings',
                    func=lambda *args: show_settings_window(self.window),
                    accel='<Primary>comma'
                ),
                AppAction(
                    name='shortcuts',
                    func=lambda *args: show_shortcuts_window(self.window),
                    accel='<Primary>question'
                ),
                AppAction(
                    name='about',
                    func=self.show_about_dialog
                ),
                AppAction(
                    name='quit',
                    func=self.on_destroy_window,
                    accel='<Primary>q'
                )
            ],
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
            css_resource='/org/gabmus/gfeeds/ui/gtk_style.css'
        )
        self.feedman = FeedsManager()

    def do_startup(self):
        super().do_startup()
        self.feedman.refresh(
            get_cached=not self.confman.conf['refresh_on_startup'],
            is_startup=True
        )

    def view_mode_change(
            self,
            action: Gio.SimpleAction,
            target: GLib.Variant,
            *args
    ):
        action.change_state(target)
        target_s = str(target).strip("'")
        if target_s not in ['webview', 'reader', 'rsscont']:
            target_s = 'webview'
        self.window.right_headerbar.on_view_mode_change(target_s)
        self.confman.conf['default_view'] = target_s
        self.confman.save_conf()

    def show_read_items(self, action: Gio.SimpleAction, *args):
        action.change_state(
            GLib.Variant.new_boolean(not action.get_state().get_boolean())
        )
        self.confman.conf['show_read_items'] = action.get_state().get_boolean()
        self.confman.emit('gfeeds_show_read_changed', '')

    def set_all_read(self, *args):
        self.window.sidebar.listview_sw.set_all_read_state(True)

    def set_all_unread(self, *args):
        self.window.sidebar.listview_sw.set_all_read_state(False)

    def manage_feeds(self, *args):
        mf_win = GFeedsManageFeedsWindow(
            self.window
        )
        mf_win.present()

    def import_opml(self, *args):
        dialog = GFeedsOpmlFileChooserDialog(self.window)

        def on_response(_dialog, res):
            if res == Gtk.ResponseType.ACCEPT:
                add_feeds_from_opml(dialog.get_file().get_path())

        dialog.connect('response', on_response)
        dialog.show()

    def export_opml(self, *args):
        dialog = GFeedsOpmlSavePathChooserDialog(self.window)

        def on_response(_dialog, res):
            if res == Gtk.ResponseType.ACCEPT:
                save_path = dialog.get_file().get_path()
                if save_path[-5:].lower() != '.opml':
                    save_path += '.opml'
                opml_out = feeds_list_to_opml(self.feedman.feeds)
                with open(save_path, 'w') as fd:
                    fd.write(opml_out)
                    fd.close()

        dialog.connect('response', on_response)
        dialog.show()

    def show_about_dialog(self, *args):
        about_builder = Gtk.Builder.new_from_resource(
            '/org/gabmus/gfeeds/aboutdialog.ui'
        )
        dialog = about_builder.get_object('aboutdialog')
        dialog.set_modal(True)
        dialog.set_transient_for(self.window)
        dialog.present()

    def on_destroy_window(self, *args):
        self.window.on_destroy()
        self.quit()

    def do_activate(self):
        super().do_activate()
        self.window = GFeedsAppWindow()
        self.confman.window = self.window
        self.window.connect('close-request', self.on_destroy_window)
        self.add_window(self.window)
        self.window.present()
        # self.feedman.refresh(get_cached=True)
        if self.args:
            if self.args.argurl:
                if self.args.argurl[:8].lower() == 'file:///':
                    abspath = self.args.argurl[7:]
                    if isfile(abspath):
                        if abspath[-5:].lower() == '.opml':
                            dialog = GFeedsConfirmAddDialog(
                                self.window, abspath
                            )
                            res = dialog.run()
                            dialog.close()
                            if res == Gtk.ResponseType.YES:
                                add_feeds_from_opml(abspath)
                        else:
                            # why no check for extension here?
                            # some websites have feeds without extension
                            # dumb but that's what it is
                            self.args.argurl = get_feed_link_from_file(
                                abspath
                            ) or ''
                if (
                        self.args.argurl[:7].lower() == 'http://' or
                        self.args.argurl[:8].lower() == 'https://'
                ):
                    dialog = GFeedsConfirmAddDialog(
                        self.window,
                        self.args.argurl,
                        http=True
                    )
                    res = dialog.run()
                    dialog.close()
                    if res == Gtk.ResponseType.YES:
                        self.feedman.add_feed(self.args.argurl)
                else:
                    print('This file is not supported')

    def do_command_line(self, args: list):
        """
        GTK.Application command line handler
        called if Gio.ApplicationFlags.HANDLES_COMMAND_LINE is set.
        must call the self.do_activate() to get the application up and running.
        """
        # call the default commandline handler
        Gtk.Application.do_command_line(self, args)
        # make a command line parser
        parser = argparse.ArgumentParser()
        parser.add_argument(
            'argurl',
            metavar=_('url'),
            type=str,
            nargs='?',
            help=_('opml file local url or rss remote url to import')
        )
        # parse the command line stored in args,
        # but skip the first element (the filename)
        self.args = parser.parse_args(args.get_arguments()[1:])
        # call the main program do_activate() to start up the app
        self.do_activate()
        return 0


def main():

    application = GFeedsApplication()

    try:
        ret = application.run(sys.argv)
    except SystemExit as e:
        ret = e.code

    sys.exit(ret)


if __name__ == '__main__':
    main()
