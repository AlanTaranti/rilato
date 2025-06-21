from posixpath import expanduser
import sys
import argparse
from gettext import gettext as _
from os.path import isfile
from gi.repository import Gtk, Gdk, Gio, GLib, Adw
from rilato.confManager import ConfManager
from rilato.feeds_manager import FeedsManager
from rilato.app_window import RilatoAppWindow
from rilato.preferences_window import show_preferences_window
from rilato.util.opml_generator import feeds_list_to_opml
from rilato.util.opml_parser import opml_to_rss_list
from rilato.opml_file_chooser import (
    RilatoOpmlFileChooserDialog,
    RilatoOpmlSavePathChooserDialog,
)
from rilato.manage_feeds_window import RilatoManageFeedsWindow
from rilato.scrolled_dialog import ScrolledDialogResponse, ScrolledDialog
from rilato.shortcuts_window import show_shortcuts_window
from rilato.util.rss_link_from_file import get_feed_link_from_file
from rilato.base_app import BaseApp, AppAction
from xml.sax.saxutils import escape


class RilatoApplication(BaseApp):
    def __init__(self):
        self.confman = ConfManager()
        super().__init__(
            app_id="org.gabmus.rilato",
            app_name="Feeds",
            app_actions=[
                AppAction(
                    name="show_read_items",
                    func=self.show_read_items,
                    accel="<Control>h",
                    stateful=True,
                    state_type=AppAction.StateType.BOOL,
                    state_default=self.confman.nconf.show_read_items,
                ),
                AppAction(
                    name="show_empty_feeds",
                    func=self.show_empty_feeds,
                    stateful=True,
                    state_type=AppAction.StateType.BOOL,
                    state_default=self.confman.nconf.show_empty_feeds,
                ),
                AppAction(
                    name="view_mode_change",
                    func=self.view_mode_change,
                    stateful=True,
                    state_type=AppAction.StateType.RADIO,
                    state_default=self.confman.nconf.default_view,
                ),
                AppAction(
                    name="set_all_read", func=self.set_all_read, accel="<Control>m"
                ),
                AppAction(name="set_all_unread", func=self.set_all_unread),
                AppAction(name="manage_feeds", func=self.manage_feeds),
                AppAction(name="import_opml", func=self.import_opml),
                AppAction(name="export_opml", func=self.export_opml),
                AppAction(
                    name="settings",
                    func=lambda *__: show_preferences_window(self.window),
                    accel="<Primary>comma",
                ),
                AppAction(
                    name="shortcuts",
                    func=lambda *__: show_shortcuts_window(self.window),
                    accel="<Primary>question",
                ),
                AppAction(name="about", func=self.show_about_dialog),
                AppAction(name="quit", func=self.on_destroy_window, accel="<Primary>q"),
                AppAction(
                    name="open_externally",
                    func=self.open_externally,
                    accel="<Control>o",
                ),
                AppAction(name="open_media_player", func=self.open_media_player),
                AppAction(name="copy_link", func=self.copy_link),
            ],
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
            css_resource="/org/gabmus/rilato/ui/gtk_style.css",
        )
        self.feedman = FeedsManager()

    def do_startup(self):
        super().do_startup()
        self.window = RilatoAppWindow(self)
        self.window.connect("close-request", self.on_destroy_window)
        self.add_window(self.window)
        self.feedman.refresh(
            get_cached=not self.confman.nconf.refresh_on_startup, is_startup=True
        )

    def open_media_player(self, *__):
        self.window.leaflet.webview.action_open_media_player()

    def open_externally(self, *__):
        self.window.leaflet.webview.open_externally()

    def copy_link(self, *__):
        Gdk.Display.get_default().get_clipboard().set(self.window.leaflet.webview.uri)
        self.window.leaflet.webview.show_notif()

    def view_mode_change(self, action: Gio.SimpleAction, target: GLib.Variant, *__):
        action.change_state(target)
        target_s = str(target).strip("'")
        if target_s not in ["webview", "reader", "feedcont"]:
            target_s = "webview"
        self.window.leaflet.on_view_mode_change(target_s)
        self.confman.nconf.default_view = target_s

    def show_read_items(self, action: Gio.SimpleAction, *__):
        action.change_state(
            GLib.Variant.new_boolean(not action.get_state().get_boolean())
        )
        self.confman.nconf.show_read_items = action.get_state().get_boolean()
        self.confman.emit("rilato_show_read_changed")

    def show_empty_feeds(self, action: Gio.SimpleAction, *__):
        action.change_state(
            GLib.Variant.new_boolean(not action.get_state().get_boolean())
        )
        self.confman.nconf.show_empty_feeds = action.get_state().get_boolean()
        self.confman.emit("rilato_show_empty_feeds_changed")

    def set_all_read(self, *__):
        self.window.leaflet.sidebar.listview_sw.set_all_read_state(True)

    def set_all_unread(self, *__):
        self.window.leaflet.sidebar.listview_sw.set_all_read_state(False)

    def manage_feeds(self, *__):
        mf_win = RilatoManageFeedsWindow(self.window)
        mf_win.present()

    def import_opml(self, *__):
        dialog = RilatoOpmlFileChooserDialog(self.window)

        def on_response(__, res):
            if res == Gtk.ResponseType.ACCEPT:
                self.feedman.import_opml(dialog.get_file().get_path())

        dialog.connect("response", on_response)
        dialog.show()

    def export_opml(self, *__):
        dialog = RilatoOpmlSavePathChooserDialog(self.window)

        def on_response(__, res):
            if res == Gtk.ResponseType.ACCEPT:
                save_path = dialog.get_file().get_path()
                if not save_path.lower().endswith(".opml"):
                    save_path += ".opml"
                opml_out = feeds_list_to_opml(self.feedman.feed_store.sort_store)
                with open(save_path, "w") as fd:
                    fd.write(opml_out)

        dialog.connect("response", on_response)
        dialog.show()

    def show_about_dialog(self, *__):
        about_builder = Gtk.Builder.new_from_resource(
            "/org/gabmus/rilato/aboutdialog.ui"
        )
        dialog = about_builder.get_object("aboutdialog")
        dialog.set_modal(True)
        dialog.set_transient_for(self.window)
        dialog.present()

    def on_destroy_window(self, *__):
        self.window.on_destroy()
        self.quit()

    def do_activate(self):
        super().do_activate()
        self.window.present()
        # self.feedman.refresh(get_cached=True)
        if self.args:
            if self.args.argurl:
                abspath = self.args.argurl.strip()
                if abspath.lower().startswith("file:///"):
                    abspath = self.args.argurl.removeprefix("file://")
                if isfile(expanduser(abspath)):
                    if abspath.lower().endswith(".opml"):

                        def on_cancel(_dialog, __):
                            _dialog.close()

                        def on_import(_dialog, __):
                            _dialog.close()
                            self.feedman.import_opml(abspath)

                        dialog = ScrolledDialog(
                            parent=self.window,
                            title=_("Do you want to import these feeds?"),
                            body=escape(
                                "\n".join([f.feed for f in opml_to_rss_list(abspath)])
                            ),
                            responses=[
                                ScrolledDialogResponse(
                                    "cancel", _("_Cancel"), on_cancel
                                ),
                                ScrolledDialogResponse(
                                    "import",
                                    _("_Import"),
                                    on_import,
                                    Adw.ResponseAppearance.SUGGESTED,
                                ),
                            ],
                        )

                        dialog.present()
                    else:
                        # why no check for extension here?
                        # some websites have feeds without extension
                        # dumb but that's what it is
                        self.args.argurl = get_feed_link_from_file(abspath) or ""
                if self.args.argurl.lower().startswith(
                    "http://"
                ) or self.args.argurl.lower().startswith("https://"):

                    def on_import(_dialog, __):
                        _dialog.close()
                        self.feedman.add_feed(argurl)

                    def on_cancel(_dialog, __):
                        _dialog.close()

                    dialog = ScrolledDialog(
                        parent=self.window,
                        title=_("Do you want to import this feed?"),
                        body=escape(self.args.argurl),
                        responses=[
                            ScrolledDialogResponse("cancel", _("_Cancel"), on_cancel),
                            ScrolledDialogResponse(
                                "import",
                                _("_Import"),
                                on_import,
                                Adw.ResponseAppearance.SUGGESTED,
                            ),
                        ],
                    )
                    argurl = self.args.argurl

                    dialog.present()
                else:
                    print("This file is not supported")
            self.args = None

    def do_command_line(self, args: Gio.ApplicationCommandLine):
        """
        GTK.Application command line handler
        called if Gio.ApplicationFlags.HANDLES_COMMAND_LINE is set.
        must call the self.do_activate() to get the application up and running.
        """
        # call the default commandline handler
        # not required anymore?
        # Gtk.Application.do_command_line(self, args)
        # make a command line parser
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "argurl",
            metavar=_("url"),
            type=str,
            nargs="?",
            help=_("opml file local url or rss remote url to import"),
        )
        # parse the command line stored in args,
        # but skip the first element (the filename)
        self.args = parser.parse_args(args.get_arguments()[1:])
        # call the main program do_activate() to start up the app
        self.do_activate()
        return 0


def main():
    application = RilatoApplication()

    try:
        ret = application.run(sys.argv)
    except SystemExit as e:
        ret = e.code

    sys.exit(ret)


if __name__ == "__main__":
    main()
