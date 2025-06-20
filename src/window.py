# window.py
#
# Copyright 2025 Taranti
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw
from gi.repository import Gtk


@Gtk.Template(resource_path="/me/alantaranti/rilato/window.ui")
class RilatoWindow(Adw.ApplicationWindow):
    __gtype_name__ = "RilatoWindow"

    label = Gtk.Template.Child()
    startup_entry = Gtk.Template.Child()
    send_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Clear entry at startup
        self.startup_entry.set_text("")

    @Gtk.Template.Callback
    def on_send_button_clicked(self, widget):
        self._send_input()

    @Gtk.Template.Callback
    def on_startup_entry_activate(self, entry):
        self._send_input()

    def _send_input(self):
        text = self.startup_entry.get_text()
        # TODO: handle sending text
        print(f"Sending input: {text}")
        self.startup_entry.set_text("")
