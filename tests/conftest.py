# conftest.py
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

import sys
import os
import pytest
from unittest.mock import MagicMock

# Add the src directory to the Python path so that imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import gi and set required versions
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Gio, Adw, GLib


@pytest.fixture
def mock_window():
    """Fixture providing a mock window."""
    window = MagicMock()
    window.present = MagicMock()
    return window


@pytest.fixture
def mock_application():
    """Fixture providing a mock application."""
    from src.main import RilatoApplication
    
    # Create a real application instance but with mocked methods
    app = RilatoApplication()
    app.quit = MagicMock()
    
    # Return the application
    yield app
    
    # Clean up
    app = None


@pytest.fixture
def gtk_main_loop():
    """Fixture providing a GLib main loop for GTK tests."""
    # Create a main loop
    loop = GLib.MainLoop()
    
    # Return the loop
    yield loop
    
    # Clean up
    if loop.is_running():
        loop.quit()