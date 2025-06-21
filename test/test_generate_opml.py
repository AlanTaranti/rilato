from unittest.mock import MagicMock
from rilato.util.opml_generator import feeds_list_to_opml


MOCK_FEEDS = [MagicMock(), MagicMock(), MagicMock()]
EXPECTED_OPML = """<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head>
    <title>Subscriptions</title>
  </head>
  <body>
    <outline type="rss" title="foo bar" text="bar baz" \
xmlUrl="http://example.org/rss" htmlUrl="http://example.org" \
category="t,tt,ttt" />
    <outline type="rss" title="foo bar" text="bar baz" \
xmlUrl="http://example.org/rss1" htmlUrl="http://example.org" \
category="" />
    <outline type="rss" title="&lt;lorem /&gt; ipsum's \
&lt;dolor &quot;sit&quot;" text='&lt;foo bar="baz"&gt;' \
xmlUrl="example.org/rss2" htmlUrl="example.org" \
category='&lt;tag&gt;,&lt;tag2 foo="bar" /&gt;' />
  </body>
</opml>"""


def __configure_mock():
    MOCK_FEEDS[0].configure_mock(
        **{
            "title": "foo bar",
            "description": "bar baz",
            "rss_link": "http://example.org/rss",
            "link": "http://example.org",
            "get_conf_dict.return_value": {"tags": ["t", "tt", "ttt"]},
        }
    )
    MOCK_FEEDS[1].configure_mock(
        **{
            "title": "foo bar",
            "description": "bar baz",
            "rss_link": "http://example.org/rss1",
            "link": "http://example.org",
            "get_conf_dict.return_value": {"tags": []},
        }
    )
    MOCK_FEEDS[2].configure_mock(
        **{
            "title": '<lorem /> ipsum\'s <dolor "sit"',
            "description": '<foo bar="baz">',
            "rss_link": "example.org/rss2",
            "link": "example.org",
            "get_conf_dict.return_value": {"tags": ["<tag>", '<tag2 foo="bar" />']},
        }
    )


def test_generate_opml():
    __configure_mock()
    opml = feeds_list_to_opml(MOCK_FEEDS)
    assert opml == EXPECTED_OPML
