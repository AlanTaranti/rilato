import unittest
from unittest.mock import Mock, MagicMock, patch, mock_open
from parameterized import parameterized
from datetime import datetime, timezone, timedelta
from .sample_rss import SAMPLE_RSS

from gfeeds.rss_parser import FeedItem, FakeFeed, Feed, FeedParser
from os import remove, makedirs, rmdir, listdir
from os.path import isfile, isdir


class TestFeedItem(unittest.TestCase):

    @parameterized.expand([
        ['2020-05-09 10:51:10+03:00'],  # RFC 3339
        ['2020-05-09T10:51:10+03:00']   # ISO
    ])
    @patch('gfeeds.rss_parser.ConfManager')
    def test_FeedItem_create(self, date, ConfManager_mock):
        confman_mock = ConfManager_mock()
        confman_mock.read_feeds_items = ['https://planet.gnome.org']
        fp_item = {
            'title': 'Test Article',
            'link': 'https://planet.gnome.org',
            'published': date
        }
        feeditem = FeedItem(fp_item, None)
        feeditem.title.should.equal('Test Article')
        feeditem.is_saved.should.be.false
        feeditem.link.should.equal('https://planet.gnome.org')
        feeditem.read.should.be.true
        # need better way to check datetime
        str(feeditem.pub_date).should.equal('2020-05-09 10:51:10+03:00')

    @patch('gfeeds.rss_parser.ConfManager')
    def test_FeedItem_create_malformed_date(self, ConfManager_mock):
        '''
        In case of malformed date, current time should be used
        '''
        confman_mock = ConfManager_mock()
        confman_mock.read_feeds_items = []
        fp_item = {
            'title': 'Test Article',
            'link': 'https://planet.gnome.org',
            'published': 'this is not a date!'
        }
        parent_feed = Mock()
        parent_feed.title = 'Fake feed for testing'
        feeditem = FeedItem(fp_item, parent_feed)
        (
            datetime.now(timezone.utc) - feeditem.pub_date
        ).seconds.should.be.lower_than(1)

    # TODO: test with atom feed, feeds with non utf encodings
    @patch('gfeeds.rss_parser.get_favicon')
    @patch('gfeeds.rss_parser.download_raw')
    @patch(
            'builtins.open',
            new_callable=mock_open,
            read_data=SAMPLE_RSS.encode()  # wants bytes
    )
    @patch('gfeeds.rss_parser.ConfManager')
    def test_Feed_create(
            self,
            ConfManager_mock,
            mock_file,
            download_raw_mock,
            get_favicon_mock
    ):
        confman_mock = ConfManager_mock()
        download_res = (
            '/some/path',  # feedpath
            'https://planet.gnome.org'  # feed link
        )
        # always have the one article selected, so alter the max article age
        confman_mock.max_article_age = (
            (
                datetime.now(timezone.utc) -
                datetime(2020, 3, 26, 15, 18, tzinfo=timezone.utc)
            ) +
            timedelta(days=100)
        )
        confman_mock.thumbs_cache_path = '/tmp/org.gabmus.gfeeds_test_thumbs'
        if isdir(confman_mock.thumbs_cache_path):
            for f in listdir(confman_mock.thumbs_cache_path):
                remove(f)
        else:
            makedirs(confman_mock.thumbs_cache_path)
        parser = FeedParser()
        parser.parse(download_res)

        parser.is_null.should.be.false
        parser.error.should.be.none
        parser.rss_link.should.equal('https://planet.gnome.org')

        # weird, testing a DOC, but feedparser is not a very stable DOC, so
        # testing it on my side has some value
        parser.fp_feed.should.be.a(dict)
        parser.fp_feed.encoding.should.equal('utf-8')
        parser.fp_feed.entries.should.have.length_of(1)

        parser.title.should.equal('Planet GNOME')
        parser.link.should.equal('https://planet.gnome.org/')
        parser.description.should.equal(
            'Planet GNOME - https://planet.gnome.org/'
        )
        parser.raw_entries.should.have.length_of(1)
        # TODO: complete this test, there's more

        # cleanup
        if isdir(confman_mock.thumbs_cache_path):
            for f in listdir(confman_mock.thumbs_cache_path):
                remove(f)
            rmdir(confman_mock.thumbs_cache_path)
