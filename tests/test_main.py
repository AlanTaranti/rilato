import sys
import pytest
from unittest.mock import patch, MagicMock, PropertyMock

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

# Mock the window module to avoid resource loading issues
sys.modules["src.window"] = MagicMock()
sys.modules["src.window"].RilatoWindow = MagicMock()

# Mock the gettext function
sys.modules["builtins"]._ = MagicMock(return_value="translator-credits")

# Import the module to test
from src.main import RilatoApplication, main  # noqa: E402


@pytest.fixture
def app():
    """Fixture providing a RilatoApplication instance."""
    app_instance = RilatoApplication()
    yield app_instance
    # Clean up resources
    app_instance = None


@pytest.mark.gtk
class TestRilatoApplication:
    """Test cases for the RilatoApplication class."""

    def test_init(self, app) -> None:
        """Test the initialization of RilatoApplication."""
        # Check application properties
        assert app.get_application_id() == "me.alantaranti.rilato"
        assert app.get_resource_base_path() == "/me/alantaranti/rilato"

        # Check that actions were created
        assert app.lookup_action("quit") is not None
        assert app.lookup_action("about") is not None
        assert app.lookup_action("preferences") is not None

    @patch("src.main.RilatoWindow")
    def test_do_activate_no_window(self, mock_window_class, app) -> None:
        """Test do_activate when no window exists."""
        # Setup mock
        mock_window = MagicMock()
        mock_window_class.return_value = mock_window

        # Mock get_windows to return an empty list (no active windows)
        with patch.object(app, "get_windows", return_value=[]):
            # Call the method
            app.do_activate()

            # Check that a new window was created and presented
            mock_window_class.assert_called_once_with(application=app)
            mock_window.present.assert_called_once()

    def test_do_activate_with_window(self, app) -> None:
        """Test do_activate when a window already exists."""
        # Setup mock for existing window
        mock_window = MagicMock()

        # Directly patch the props.active_window property getter
        with patch(
            "gi.repository.Gio.Application.props", new_callable=PropertyMock
        ) as mock_props:
            mock_props.return_value.active_window = mock_window

            # Call the method
            app.do_activate()

            # Check that existing window was presented
            mock_window.present.assert_called_once()

    @patch("src.main.Adw.AboutDialog")
    def test_on_about_action(self, mock_about_dialog, app) -> None:
        """Test the on_about_action method."""
        # Setup mocks
        mock_dialog = MagicMock()
        mock_about_dialog.return_value = mock_dialog
        mock_window = MagicMock()

        # Directly patch the props.active_window property getter
        with patch(
            "gi.repository.Gio.Application.props", new_callable=PropertyMock
        ) as mock_props:
            mock_props.return_value.active_window = mock_window

            # Call the method
            app.on_about_action()

            # Check that AboutDialog was created with correct parameters
            mock_about_dialog.assert_called_once()
            # Verify dialog properties
            assert mock_about_dialog.call_args[1]["application_name"] == "rilato"
            assert (
                mock_about_dialog.call_args[1]["application_icon"]
                == "me.alantaranti.rilato"
            )
            assert mock_about_dialog.call_args[1]["developer_name"] == "Alan Taranti"
            assert mock_about_dialog.call_args[1]["version"] == "0.1.0"
            assert mock_about_dialog.call_args[1]["developers"] == ["Alan Taranti"]
            assert mock_about_dialog.call_args[1]["copyright"] == "© 2025 Alan Taranti"

            # Check that dialog was presented
            mock_dialog.present.assert_called_once_with(mock_window)

    @patch("builtins.print")
    def test_on_preferences_action(self, mock_print, app) -> None:
        """Test the on_preferences_action method."""
        # Call the method
        app.on_preferences_action(None, None)

        # Check that print was called with the correct message
        mock_print.assert_called_once_with("app.preferences action activated")

    def test_create_action(self, app) -> None:
        """Test the create_action method."""
        # Mock callback
        mock_callback = MagicMock()

        # Create a test action
        app.create_action("test_action", mock_callback, ["<primary>t"])

        # Check that action was added
        action = app.lookup_action("test_action")
        assert action is not None

        # Activate the action and check that callback was called
        action.activate(None)
        mock_callback.assert_called_once()

        # Check that accelerator was set
        accels = app.get_accels_for_action("app.test_action")
        # Note: '<primary>t' is translated to '<Control>t' on most platforms
        assert accels == ["<Control>t"]

    @pytest.mark.parametrize("version", ["0.1.0", "1.0.0"])
    @patch("src.main.RilatoApplication.run")
    def test_main(self, mock_run, version) -> None:
        """Test the main function."""
        # Setup mock
        mock_run.return_value = 0

        # Call the function
        result = main(version)

        # Check that app.run was called with sys.argv
        mock_run.assert_called_once_with(sys.argv)

        # Check return value
        assert result == 0
