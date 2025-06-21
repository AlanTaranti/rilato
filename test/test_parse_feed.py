from pathlib import Path
from .sample_rss import SAMPLE_RSS
from rilato.feed_parser import parse_feed
from os import remove
import pytest


RSS_PATH = '/tmp/org.gabmus.rilato.test.parse_feed.rss'


@pytest.fixture(autouse=True)
def run_around_tests():
    with open(RSS_PATH, 'w') as fd:
        fd.write(SAMPLE_RSS)
    yield
    remove(RSS_PATH)


def test_parse_feed():
    res = parse_feed(Path(RSS_PATH))
    assert not res.is_null
    assert res.error is None
    assert res.title == 'GabMus\'s Dev Log'
    assert res.description == 'Recent content on GabMus\'s Dev Log'
    assert res.image_url == 'https://gabmus.org/logo.svg'
    assert res.link == 'https://gabmus.org/'
    assert res.rss_link == 'https://gabmus.org/index.xml'
    assert len(res.raw_entries) == 5
