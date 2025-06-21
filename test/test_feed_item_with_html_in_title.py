from os import remove
from pathlib import Path
import pytest
from rilato.feed_item import FeedItem
from rilato.feed_parser import parse_feed

RSS_PATH = "/tmp/org.gabmus.rilato.test.feed_item_with_html_in_title.rss"
SAMPLE_RSS = """<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<?xml-stylesheet href="/feed_style.xsl" type="text/xsl"?>
<rss version="2.0"
    xmlns:atom="http://www.w3.org/2005/Atom"
    xmlns:media="https://www.rssboard.org/media-rss">
    <channel>
        <title>GabMus&#39;s Dev Log</title>
        <link>https://gabmus.org/</link>
        <description>Recent content on GabMus&#39;s Dev Log</description>
        <generator>Hugo -- gohugo.io</generator>
        <language>en-us</language>
        <copyright>Gabriele Musco - [Creative Commons Attribution 4.0 \
International License](https://creativecommons.org/licenses/by/4.0/).\
</copyright>
        <lastBuildDate>Mon, 14 Feb 2022 11:31:20 +0100</lastBuildDate>
        <atom:link href="https://gabmus.org/index.xml" rel="self" \
type="application/rss+xml" />
        <icon>https://gabmus.org/logo.svg</icon>
        <item>
            <title><![CDATA[<p>foo <strong>bar</strong> baz</p>]]></title>
            <link>https://gabmus.org/posts/swatch_a_color_palette_manager/\
</link>
            <pubDate>Mon, 14 Feb 2022 11:31:20 +0100</pubDate>
            <guid>https://gabmus.org/posts/swatch_a_color_palette_manager/\
</guid>
            <description>
                <![CDATA[<p>foo bar baz</p>]]>
            </description>
            <media:thumbnail url="https://gabmus.org/images/post_pics/\
Swatch_a_color_palette_manager/scrot0.png" />
        </item>
    </channel>
</rss>
"""


@pytest.fixture(autouse=True)
def run_around_tests():
    with open(RSS_PATH, "w") as fd:
        fd.write(SAMPLE_RSS)
    yield
    remove(RSS_PATH)


class MockNConf:
    read_items = []


def __mock_confman(monkeypatch):
    class MockConfManager:
        def __init__(self):
            self.nconf = MockNConf()

    monkeypatch.setattr("rilato.feed_item.ConfManager", MockConfManager)


def test_feed_item_with_html_in_title(monkeypatch):
    __mock_confman(monkeypatch)
    feed = parse_feed(Path(RSS_PATH))
    assert len(feed.raw_entries) == 1
    fi = FeedItem(feed.raw_entries[0], feed)
    assert fi.title == "foo bar baz"
