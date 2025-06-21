from typing import List, Optional, Dict, Any
import os
from datetime import datetime
import dateutil.parser
from lxml import etree
import pytz


class FeedItem:
    """
    A replacement for the syndom.FeedItem class using lxml.
    """

    def __init__(self, item_element: etree.Element, namespaces: Dict[str, str]):
        """
        Initialize the FeedItem object with an XML element.

        Args:
            item_element: The XML element representing the feed item
            namespaces: XML namespaces dictionary
        """
        self.element = item_element
        self.namespaces = namespaces
        self._uri = None
        self._title = None
        self._description = None
        self._content = None
        self._pub_date = None
        self._author = None
        self._categories = None

    def get_url(self) -> Optional[str]:
        """Get the URL of the feed item."""
        if self._uri is None:
            # Try different tags for the URL
            for tag in ["link", "{http://www.w3.org/2005/Atom}link"]:
                link = self.element.find(tag, self.namespaces)
                if link is not None:
                    if link.get("href"):  # Atom format
                        self._uri = link.get("href")
                        break
                    elif link.text:  # RSS format
                        self._uri = link.text
                        break
        return self._uri

    @property
    def uri(self) -> Optional[str]:
        """Get the URL of the feed item."""
        return self.get_url()

    def get_title(self) -> Optional[str]:
        """Get the title of the feed item."""
        if self._title is None:
            title_elem = self.element.find("title", self.namespaces)
            if title_elem is None:
                title_elem = self.element.find(
                    "{http://www.w3.org/2005/Atom}title", self.namespaces
                )

            if title_elem is not None:
                try:
                    # Get the full XML content of the title element, including CDATA sections
                    from lxml import etree
                    from bs4 import BeautifulSoup

                    # Convert the element to a string, including all its content
                    xml_str = etree.tostring(
                        title_elem, encoding="unicode", method="xml"
                    )

                    # Extract just the content between the title tags
                    if "<title>" in xml_str and "</title>" in xml_str:
                        content = xml_str.split("<title>", 1)[1].split("</title>")[0]
                    elif "<ns:title>" in xml_str and "</ns:title>" in xml_str:
                        content = xml_str.split("<ns:title>", 1)[1].split(
                            "</ns:title>"
                        )[0]
                    else:
                        content = title_elem.text or ""

                    # Parse the content with BeautifulSoup to extract the text
                    soup = BeautifulSoup(content, features="lxml")
                    self._title = soup.text.strip()
                except (ImportError, Exception):
                    # If there's an error, fall back to using the text attribute
                    self._title = title_elem.text
        return self._title

    @property
    def title(self) -> Optional[str]:
        """Get the title of the feed item."""
        return self.get_title()

    def get_description(self) -> Optional[str]:
        """Get the description of the feed item."""
        if self._description is None:
            # Try different tags for the description
            for tag in [
                "description",
                "summary",
                "{http://www.w3.org/2005/Atom}summary",
            ]:
                desc = self.element.find(tag, self.namespaces)
                if desc is not None and desc.text:
                    self._description = desc.text
                    break
        return self._description

    @property
    def description(self) -> Optional[str]:
        """Get the description of the feed item."""
        return self.get_description()

    def get_content(self) -> Optional[str]:
        """Get the content of the feed item."""
        if self._content is None:
            # Try different tags for the content
            for tag in [
                "content",
                "{http://purl.org/rss/1.0/modules/content/}encoded",
                "{http://www.w3.org/2005/Atom}content",
            ]:
                try:
                    content = self.element.find(tag, self.namespaces)
                    if content is not None:
                        if content.text:
                            self._content = content.text
                            break
                except Exception:
                    # Ignore errors with namespace prefixes
                    continue
        return self._content or self.get_description()

    @property
    def content(self) -> Optional[str]:
        """Get the content of the feed item."""
        return self.get_content()

    def get_pub_date(self) -> Optional[datetime]:
        """Get the publication date of the feed item."""
        if self._pub_date is None:
            # Try different tags for the publication date
            for tag in [
                "pubDate",
                "published",
                "updated",
                "{http://www.w3.org/2005/Atom}published",
                "{http://www.w3.org/2005/Atom}updated",
            ]:
                date = self.element.find(tag, self.namespaces)
                if date is not None and date.text:
                    try:
                        dt = dateutil.parser.parse(date.text)
                        if dt.tzinfo is None:
                            dt = pytz.UTC.localize(dt)
                        self._pub_date = dt
                        break
                    except (ValueError, OverflowError):
                        continue
        return self._pub_date

    @property
    def pub_date(self) -> Optional[datetime]:
        """Get the publication date of the feed item."""
        return self.get_pub_date()

    def get_author(self) -> Optional[str]:
        """Get the author of the feed item."""
        if self._author is None:
            # Try different tags for the author
            for tag in [
                "author",
                "{http://purl.org/dc/elements/1.1/}creator",
                "{http://www.w3.org/2005/Atom}author",
            ]:
                try:
                    author = self.element.find(tag, self.namespaces)
                    if author is not None:
                        if author.text:  # RSS format
                            self._author = author.text
                            break
                        # Atom format
                        name = author.find(
                            "{http://www.w3.org/2005/Atom}name", self.namespaces
                        )
                        if name is not None and name.text:
                            self._author = name.text
                            break
                except Exception:
                    # Ignore errors with namespace prefixes
                    continue
        return self._author

    def get_author_name(self) -> Optional[str]:
        """Get the name of the author of the feed item."""
        return self.get_author()

    def get_author_url(self) -> Optional[str]:
        """Get the URL of the author of the feed item."""
        # Try to find author URL in Atom format
        author = self.element.find(
            "{http://www.w3.org/2005/Atom}author", self.namespaces
        )
        if author is not None:
            uri = author.find("{http://www.w3.org/2005/Atom}uri", self.namespaces)
            if uri is not None and uri.text:
                return uri.text
        return None

    def get_img_url(self) -> Optional[str]:
        """Get the image URL of the feed item."""
        # Try to find media:thumbnail
        try:
            thumbnail = self.element.find(
                "{https://www.rssboard.org/media-rss}thumbnail", self.namespaces
            )
            if thumbnail is not None and thumbnail.get("url"):
                return thumbnail.get("url")
        except Exception:
            # Ignore errors with namespace prefixes
            pass

        # Try to find enclosure
        enclosure = self.element.find("enclosure", self.namespaces)
        if enclosure is not None and enclosure.get("url"):
            return enclosure.get("url")

        return None

    @property
    def author(self) -> Optional[str]:
        """Get the author of the feed item."""
        return self.get_author()

    def get_categories(self) -> List[str]:
        """Get the categories of the feed item."""
        if self._categories is None:
            self._categories = []
            for category in self.element.findall("category", self.namespaces):
                if category.text:
                    self._categories.append(category.text)
                elif category.get("term"):  # Atom format
                    self._categories.append(category.get("term"))
        return self._categories

    @property
    def categories(self) -> List[str]:
        """Get the categories of the feed item."""
        return self.get_categories()


class Feed:
    """
    A replacement for the syndom.Feed class using lxml.
    """

    def __init__(self, file_path: str):
        """
        Initialize the Feed object with the content of the file at file_path.

        Args:
            file_path: Path to the feed file (XML/RSS/Atom)
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        self.file_path = file_path
        self.tree = etree.parse(file_path)
        self.root = self.tree.getroot()

        # Extract namespaces
        self.namespaces = {k if k else "ns": v for k, v in self.root.nsmap.items()}

        # Determine feed type (RSS or Atom)
        self.is_atom = self.root.tag.endswith("feed")

        # Cache for feed items
        self._items = None

    def get_title(self) -> Optional[str]:
        """Get the title of the feed."""
        if self.is_atom:
            # For Atom feeds
            title = self.root.find(
                ".//{http://www.w3.org/2005/Atom}title", self.namespaces
            )
        else:
            # For RSS feeds, look for title inside channel
            title = self.root.find(".//channel/title", self.namespaces)
            if title is None:
                # Fallback to any title
                title = self.root.find(".//title", self.namespaces)
        return title.text if title is not None and title.text else None

    def get_url(self) -> Optional[str]:
        """Get the URL of the feed."""
        if self.is_atom:
            # For Atom feeds, look for the alternate link
            for link in self.root.findall(
                ".//{http://www.w3.org/2005/Atom}link", self.namespaces
            ):
                if link.get("rel") == "alternate" and link.get("href"):
                    return link.get("href")
        else:
            # For RSS feeds, look for the link element
            link = self.root.find(".//link", self.namespaces)
            if link is not None and link.text:
                return link.text
        return None

    def get_rss_url(self) -> Optional[str]:
        """Get the RSS URL of the feed."""
        # Look for atom:link with rel="self"
        for link in self.root.findall(".//link", self.namespaces) + self.root.findall(
            ".//{http://www.w3.org/2005/Atom}link", self.namespaces
        ):
            if link.get("rel") == "self" and link.get("href"):
                return link.get("href")
        # If not found, try to use the URL of the feed file itself
        if self.file_path.startswith("http"):
            return self.file_path
        return None

    def get_description(self) -> Optional[str]:
        """Get the description of the feed."""
        # Try different tags for the description
        for tag in [
            ".//description",
            ".//subtitle",
            ".//{http://www.w3.org/2005/Atom}subtitle",
        ]:
            desc = self.root.find(tag, self.namespaces)
            if desc is not None and desc.text:
                return desc.text
        return None

    def get_img_url(self) -> Optional[str]:
        """Get the image URL of the feed."""
        if self.is_atom:
            # For Atom feeds, look for the logo element
            logo = self.root.find(
                ".//{http://www.w3.org/2005/Atom}logo", self.namespaces
            )
            if logo is not None and logo.text:
                return logo.text
        else:
            # For RSS feeds, look for the image/url element
            img_url = self.root.find(".//image/url", self.namespaces)
            if img_url is not None and img_url.text:
                return img_url.text

            # Also look for the icon element
            icon = self.root.find(".//channel/icon", self.namespaces)
            if icon is not None and icon.text:
                return icon.text
        return None

    def get_items(self) -> List[FeedItem]:
        """Get the items of the feed."""
        if self._items is None:
            self._items = []
            if self.is_atom:
                # For Atom feeds, look for entry elements
                for entry in self.root.findall(
                    ".//{http://www.w3.org/2005/Atom}entry", self.namespaces
                ):
                    self._items.append(FeedItem(entry, self.namespaces))
            else:
                # For RSS feeds, look for item elements
                for item in self.root.findall(".//item", self.namespaces):
                    self._items.append(FeedItem(item, self.namespaces))
        return self._items


class Opml:
    """
    A replacement for the syndom.Opml class using lxml.
    """

    def __init__(self, file_path: str, include_categories: bool = False):
        """
        Initialize the Opml object with the content of the file at file_path.

        Args:
            file_path: Path to the OPML file
            include_categories: Whether to include categories in the output
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        self.file_path = file_path
        self.include_categories = include_categories
        self.tree = etree.parse(file_path)
        self.root = self.tree.getroot()

        # Extract namespaces
        self.namespaces = {k if k else "ns": v for k, v in self.root.nsmap.items()}

        # Cache for outline items
        self._items = None

    def get_items(self) -> List[Any]:
        """Get the outline items of the OPML file."""
        if self._items is None:
            self._items = []
            for outline in self.root.findall(".//outline", self.namespaces):
                # Check if this is a feed outline (has xmlUrl attribute)
                xml_url = outline.get("xmlUrl")
                if xml_url:
                    item = OpmlItem(outline, self.include_categories)
                    self._items.append(item)
        return self._items


class OpmlItem:
    """
    A class representing an item in an OPML file.
    """

    def __init__(self, element: etree.Element, include_categories: bool = False):
        """
        Initialize the OpmlItem object with an XML element.

        Args:
            element: The XML element representing the OPML item
            include_categories: Whether to include categories in the output
        """
        self.element = element
        self.include_categories = include_categories

    def get_feed_url(self) -> str:
        """Get the feed URL of the OPML item."""
        return self.element.get("xmlUrl", "")

    def get_categories(self) -> List[str]:
        """Get the categories of the OPML item."""
        if not self.include_categories:
            return []

        categories = []

        # Check for category attribute
        category = self.element.get("category")
        if category:
            categories.extend([c.strip() for c in category.split(",")])

        # Check for parent folders as categories
        parent = self.element.getparent()
        while parent is not None and parent.tag == "outline":
            title = parent.get("title") or parent.get("text")
            if title:
                categories.append(title)
            parent = parent.getparent()

        return categories
