from bs4 import BeautifulSoup
import os
from typing import Optional


class Html:
    """
    A replacement for the syndom.Html class using BeautifulSoup.
    """

    def __init__(self, file_path: str):
        """
        Initialize the Html object with the content of the file at file_path.

        Args:
            file_path: Path to the HTML file
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            self.content = f.read()

        self.soup = BeautifulSoup(self.content, "html.parser")

    @property
    def rss_url(self) -> Optional[str]:
        """
        Get the RSS feed URL from the HTML.

        Returns:
            The RSS feed URL or None if not found
        """
        # Look for RSS link in <link> tags
        for link in self.soup.find_all("link"):
            rel = link.get("rel", "")
            if isinstance(rel, list):
                rel = " ".join(rel)

            if (
                "rss" in rel.lower()
                or "atom" in rel.lower()
                or "feed" in rel.lower()
                or "alternate" in rel.lower()
            ):
                href = link.get("href")
                if href:
                    return href

        return None

    @property
    def icon_url(self) -> Optional[str]:
        """
        Get the favicon URL from the HTML.

        Returns:
            The favicon URL or None if not found
        """
        # Look for favicon in <link> tags
        for link in self.soup.find_all("link"):
            rel = link.get("rel", "")
            if isinstance(rel, list):
                rel = " ".join(rel)

            if "icon" in rel.lower() or "shortcut icon" in rel.lower():
                href = link.get("href")
                if href:
                    return href

        # If no favicon found in link tags, try the default location
        return "/favicon.ico"

    @property
    def img_url(self) -> Optional[str]:
        """
        Get the first image URL from the HTML.

        Returns:
            The image URL or None if not found
        """
        # First try to find og:image meta tag
        og_image = self.soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            return og_image.get("content")

        # Then try to find twitter:image meta tag
        twitter_image = self.soup.find("meta", {"name": "twitter:image"})
        if twitter_image and twitter_image.get("content"):
            return twitter_image.get("content")

        # Finally, look for the first image in the content
        img = self.soup.find("img")
        if img and img.get("src"):
            return img.get("src")

        return None
