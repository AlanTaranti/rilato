from gfeeds.util.opml_parser import FeedImportData, opml_to_rss_list
from os import remove
import pytest


OPML_PATH = '/tmp/org.gabmus.gfeeds.test.opml_parse.opml'
OPML_CONTENT = '''<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="https://images.ruk.ca/opml/opml.xsl"?>
<opml version="2.0">
  <head>
    <title>Peter Rukavina's Blogroll</title>
    <dateCreated>Fri, 08 May 2021 13:26:32</dateCreated>
  </head>
<body>
    <outline text="Art and Design">
      <outline text="Austin Kleon" type="rss" \
xmlUrl="https://austinkleon.com/feed/" \
htmlUrl="https://austinkleon.com/" description=""/>
      <outline text="CJ Chilvers" type="rss" \
xmlUrl="https://www.cjchilvers.com/blog?format=rss" \
htmlUrl="https://www.cjchilvers.com/blog/" description=""/>
    </outline>
    <outline text="Friends">
      <outline text="Andrea Ledwell" type="rss" \
xmlUrl="https://andrealedwell.com/?feed=rss2" \
htmlUrl="https://andrealedwell.com/" \
description="writer • designer • curious cat"/>
      <outline text="Bruce MacNaughton" type="rss" \
xmlUrl="https://preservecompany.com/blogs/bruces-muses.atom" \
htmlUrl="https://preservecompany.com/blogs/bruces-muses" description=""/>
      <outline text="Close">
        <outline text="Clark MacLeod" type="rss" \
xmlUrl="https://kelake.org/feed/" \
htmlUrl="http://www.kelake.org" \
description="Clark MacLeod's banal weblog"/>
      </outline>
    </outline>
    <outline text="Letterpress and Type">
      <outline text="Alphabettes" type="rss" \
xmlUrl="http://www.alphabettes.org/feed/" \
htmlUrl="http://www.alphabettes.org" description=""/>
    </outline>
    <outline text="silverorange" type="rss" \
xmlUrl="https://blog.silverorange.com/feed" \
htmlUrl="https://blog.silverorange.com?source=rss----c71c42b6b076---4" \
description="The collective thoughts of web design and development \
firm silverorange, Inc. - Medium"/>
  </body>
</opml>'''


@pytest.fixture(autouse=True)
def run_around_tests():
    with open(OPML_PATH, 'w') as fd:
        fd.write(OPML_CONTENT)
    yield
    remove(OPML_PATH)


def test_opml_parse():
    res = opml_to_rss_list(OPML_PATH)
    assert len(res) == 7
    assert FeedImportData(
        'https://austinkleon.com/feed/',
        ['Art and Design']
    ) in res
    assert FeedImportData(
        'https://www.cjchilvers.com/blog?format=rss',
        ['Art and Design']
    ) in res
    assert FeedImportData(
        'https://andrealedwell.com/?feed=rss2',
        ['Friends']
    ) in res
    assert FeedImportData(
        'https://preservecompany.com/blogs/bruces-muses.atom',
        ['Friends']
    ) in res
    assert FeedImportData(
        'https://kelake.org/feed/',
        ['Friends', 'Close']
    ) in res
    assert FeedImportData(
        'http://www.alphabettes.org/feed/',
        ['Letterpress and Type']
    ) in res
    assert FeedImportData(
        'https://blog.silverorange.com/feed',
        []
    ) in res
