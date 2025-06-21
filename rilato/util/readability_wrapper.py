# flake8: noqa

# Stub implementation for readability-lxml
# This is a placeholder that provides minimal functionality
# to allow the application to start without the readability package

import logging

# Create a logger to mimic the one from readability
log = logging.getLogger("readability.readability")


class RDoc:
    """
    Stub implementation of the RDoc class from readability_wrapper.
    This provides minimal functionality to allow the application to start.
    """

    def __init__(self, html, *args, **kwargs):
        self.html = html
        self.min_text_length = 25
        self._warning_shown = False

    def summary(self, **kwargs):
        """Return a simplified version of the HTML with a warning message."""
        if not self._warning_shown:
            print(
                "WARNING: Reader mode is not available because the 'readability-lxml' package is not installed."
            )
            self._warning_shown = True

        return """
        <html>
        <head><title>Reader Mode Not Available</title></head>
        <body>
            <h1>Reader Mode Not Available</h1>
            <p>The reader mode feature requires the 'readability-lxml' package, which is not installed.</p>
            <p>Please install it using: <code>pip install readability-lxml</code></p>
            <p>Or view the content in normal mode.</p>
        </body>
        </html>
        """

    def short_title(self):
        """Return a placeholder title."""
        return "Reader Mode Not Available"

    def _html(self):
        """Return an empty list as a placeholder for HTML elements."""
        return []

    def tags(self, *args):
        """Return an empty list as a placeholder for HTML tags."""
        return []

    def score_node(self, node):
        """Return a placeholder score for a node."""
        return {"content_score": 0}

    def get_link_density(self, elem):
        """Return a placeholder link density."""
        return 0

    def transform_misused_divs_into_paragraphs(self):
        """Placeholder method."""
        pass

    def score_paragraphs(self):
        """Return an empty dict as a placeholder for paragraph scores."""
        return {}
