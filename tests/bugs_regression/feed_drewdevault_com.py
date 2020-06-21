FEED_STR='''
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
	<channel>
		<title>Drew DeVault's Blog</title>
		<description>I write software. Occasionally, I will compose a post for this blog.</description>
        <link>https://drewdevault.com</link>
        <atom:link href="https://drewdevault.com/feed.xml" rel="self" type="application/rss+xml" />

			<item>
				<title>Email service provider recommendations</title>
				<description>&lt;p&gt;Email is important to my daily workflow, and I’ve built many tools which
encourage productive use of it for software development. As such, I’m often
asked for advice on choosing a good email service providers. Personally, I run
my own mail servers, but about a year ago I signed up for and evaluated many
different service providers available today so that I could make informed
recommendations to people. Here are my top picks, as well as the criteria by
which they were evaluated.&lt;/p&gt;

&lt;p&gt;Unfortunately, almost all mail providers fail to meet my criteria.  As such, I
can only recommend two: Migadu and mailbox.org.&lt;/p&gt;

&lt;h1 id=&quot;1-migadu&quot;&gt;#1: Migadu&lt;/h1&gt;

&lt;p&gt;&lt;a href=&quot;https://www.migadu.com/en/index.html&quot;&gt;Migadu&lt;/a&gt; is my go-to recommendation
for a mail service provider.&lt;/p&gt;

&lt;p&gt;&lt;strong&gt;Advantages&lt;/strong&gt;&lt;/p&gt;

&lt;ul&gt;
  &lt;li&gt;Migadu is a small company with strong values and no outside capital (i.e.
no profit-motivated external influence). Email support and a human being
answers, and their leadership is accessible if you have questions or feedback.&lt;/li&gt;
  &lt;li&gt;Their pricing is based on bandwidth usage, and does not rely on artificial
scarcity like limited domain names or mailboxes.&lt;/li&gt;
  &lt;li&gt;Has lots of features for your postmaster - you can treat it as a managed mail
server for your organization.&lt;/li&gt;
&lt;/ul&gt;

&lt;p&gt;&lt;strong&gt;Disadvantages&lt;/strong&gt;&lt;/p&gt;

&lt;ul&gt;
  &lt;li&gt;They have suffered from some outages in the past. The global mail system is
tolerant of such outages - you don’t have to worry about messages being lost
if they were sent during an outage. Still, being unable to access your mail is
a problem.&lt;/li&gt;
  &lt;li&gt;If you are on a trial account, they will put an advertisement into your email
signature. I don’t think that it’s ever appropriate for a mail service
provider to edit your outgoing emails for any reason, and certainly not to
advertise.&lt;/li&gt;
&lt;/ul&gt;

&lt;p&gt;Full disclosure: SourceHut and Migadu agreed to a consulting arrangement to
build their &lt;a href=&quot;https://git.sr.ht/~emersion/alps&quot;&gt;new webmail system&lt;/a&gt;, which should
be going into production soon. However, I had evaluated and started recommending
Migadu prior to the start of this project, and I believe that Migadu fares well
under the criteria I give at the end of this post.&lt;/p&gt;

&lt;h1 id=&quot;2-mailboxorg&quot;&gt;#2: mailbox.org&lt;/h1&gt;

&lt;p&gt;&lt;a href=&quot;https://mailbox.org/en/&quot;&gt;Mailbox.org&lt;/a&gt; may be desirable if you wish to have a
more curated experience, and less hands-on access to postmaster-specific
features.&lt;/p&gt;

&lt;p&gt;&lt;strong&gt;Advantages&lt;/strong&gt;&lt;/p&gt;

&lt;ul&gt;
  &lt;li&gt;Excellent first-class support for PGP, and many other strong security and
privacy features are available.&lt;/li&gt;
  &lt;li&gt;Was able to speak to the CEO directly to discuss my concerns and feedback, and
have my questions answered. Raised some bugs and they were fixed in short
order.&lt;/li&gt;
&lt;/ul&gt;

&lt;p&gt;&lt;strong&gt;Disadvantages&lt;/strong&gt;&lt;/p&gt;

&lt;ul&gt;
  &lt;li&gt;The interface is a little bit too JavaScript heavy for my tastes, and suffer
from some bugs and lack of polish.&lt;/li&gt;
  &lt;li&gt;They are a German company serving mostly German customers - German text leaks
into the UI and documentation in some places.&lt;/li&gt;
  &lt;li&gt;Completing a Google captcha is required to sign up.&lt;/li&gt;
&lt;/ul&gt;

&lt;h1 id=&quot;others&quot;&gt;Others&lt;/h1&gt;

&lt;p&gt;Evaluated but not recommended: disroot, fastmail, posteo.de, poste.io,
protonmail, tutanota, riseup, cock.li, teknik, runbox, megacorp mail (gmail,
outlook, etc).&lt;/p&gt;

&lt;h1 id=&quot;criteria-for-a-good-mail-service-provider&quot;&gt;Criteria for a good mail service provider&lt;/h1&gt;

&lt;p&gt;The following criteria are objective and non-negotiable:&lt;/p&gt;

&lt;ol&gt;
  &lt;li&gt;Support for open standards including IMAP and SMTP&lt;/li&gt;
  &lt;li&gt;Support for users who wish to bring their own domain&lt;/li&gt;
&lt;/ol&gt;

&lt;p&gt;This is necessary to preserve the user’s ownership of their data by making it
accessible over open and standardized protocols, and their right to move to
another service provider by not fixing their identity to a domain name
controlled by the email provider. It is for these reasons that Posteo,
ProtonMail, and Tutanota are not considered suitable.&lt;/p&gt;

&lt;p&gt;The remaining criteria are subjective:&lt;/p&gt;

&lt;ol&gt;
  &lt;li&gt;Is the business conducted ethically? Are their incentives aligned with their
customers, or with their investors?&lt;/li&gt;
  &lt;li&gt;Is it sustainable? Can I expect them to be around in 10 years? 20? 30?&lt;/li&gt;
  &lt;li&gt;Do they make unfounded claims about security or privacy, or develop
techniques which ultimately rely on trusting them instead of supporting or
improving standards which rely on encryption?&lt;sup id=&quot;fnref:1&quot;&gt;&lt;a href=&quot;#fn:1&quot; class=&quot;footnote&quot;&gt;1&lt;/a&gt;&lt;/sup&gt;&lt;/li&gt;
  &lt;li&gt;If they make claims about privacy or security, do they explain the
limitations and trade-offs, or do they let you believe it’s infallible?&lt;/li&gt;
  &lt;li&gt;Do you trust them with your personal data? What if they’re compelled by law
enforcement? What is their government like?&lt;sup id=&quot;fnref:2&quot;&gt;&lt;a href=&quot;#fn:2&quot; class=&quot;footnote&quot;&gt;2&lt;/a&gt;&lt;/sup&gt;&lt;/li&gt;
&lt;/ol&gt;

&lt;p&gt;Bonus points:&lt;/p&gt;

&lt;ul&gt;
  &lt;li&gt;What is their relationship with open source?&lt;/li&gt;
  &lt;li&gt;Can I sign up without an existing email address? Is there a chicken and egg
problem here?&lt;sup id=&quot;fnref:3&quot;&gt;&lt;a href=&quot;#fn:3&quot; class=&quot;footnote&quot;&gt;3&lt;/a&gt;&lt;/sup&gt;&lt;/li&gt;
  &lt;li&gt;How well do they handle plaintext email? Do they meet the criteria for
recommended clients at
&lt;a href=&quot;https://useplaintext.email/#implementation-recommendations&quot;&gt;useplaintext.email&lt;/a&gt;?&lt;/li&gt;
&lt;/ul&gt;

&lt;p&gt;If you represent a mail service provider which you believe meets this criteria,
please &lt;a href=&quot;mailto:sir@cmpwn.com&quot;&gt;send me an email&lt;/a&gt;.&lt;/p&gt;

&lt;div class=&quot;footnotes&quot;&gt;
  &lt;ol&gt;
    &lt;li id=&quot;fn:1&quot;&gt;
      &lt;p&gt;This also rules out ProtonMail and Tutanota, doubly damning them, especially because it provides an excuse for skipping IMAP and SMTP, which conveniently enables vendor lock-in. &lt;a href=&quot;#fnref:1&quot; class=&quot;reversefootnote&quot;&gt;&amp;#8617;&lt;/a&gt;&lt;/p&gt;
    &lt;/li&gt;
    &lt;li id=&quot;fn:2&quot;&gt;
      &lt;p&gt;This rules out Fastmail because of their government (Australlia)’s hostile and subversive laws regarding encryption. &lt;a href=&quot;#fnref:2&quot; class=&quot;reversefootnote&quot;&gt;&amp;#8617;&lt;/a&gt;&lt;/p&gt;
    &lt;/li&gt;
    &lt;li id=&quot;fn:3&quot;&gt;
      &lt;p&gt;Alarmingly rare, this one. It seems to be either this, or a captcha like mailbox.org does. I would be interested in seeing the use of client-side proof of work, or requiring someone to enter their payment details and successfully complete a charge instead. &lt;a href=&quot;#fnref:3&quot; class=&quot;reversefootnote&quot;&gt;&amp;#8617;&lt;/a&gt;&lt;/p&gt;
    &lt;/li&gt;
  &lt;/ol&gt;
&lt;/div&gt;
</description>
				<pubDate>Fri, 19 Jun 2020 00:00:00 +0000</pubDate>
                <link>https://drewdevault.com/2020/06/19/Mail-service-provider-recommendations.html</link>
		<guid isPermaLink="true">https://drewdevault.com/2020/06/19/Mail-service-provider-recommendations.html</guid>
			</item>
	</channel>
</rss>
'''


import gi
gi.require_version('Gtk', '3.0')
import unittest
from unittest.mock import Mock, MagicMock, patch
import httpretty
import sure
import sys
from os import remove, makedirs, rmdir
from os.path import isfile
from gfeeds.confManager import ConfManager
sys.modules['gfeeds.confManager'].ConfManager = Mock(ConfManager)
from gfeeds.download_manager import (
    download_feed
)
from gfeeds.rss_parser import Feed
import warnings
from datetime import timedelta

class TestDownloadManagerDrewdevaultCom(unittest.TestCase):

    def setUp(self):
        warnings.filterwarnings(
            "ignore",
            category=ResourceWarning,
            message="unclosed.*"
        )

    @patch('gfeeds.download_manager.confman')
    @patch('gfeeds.rss_parser.ConfManager')
    @httpretty.activate
    def test_feed(self, ConfManager_mock_class, mock_confman):
        rss_parser_mock_confman = ConfManager_mock_class()
        url = 'https://drewdevault.com/feed.xml'
        httpretty.register_uri(
            httpretty.GET,
            url,
            body=FEED_STR
        )
        cache_path = '/tmp'
        feed_filename = 'org.gabmus.gfeeds_test_mock_feed_path_sha'
        feed_destpath = f'{cache_path}/{feed_filename}'
        mock_confman.conf = {'feeds': {url: {}}}
        rss_parser_mock_confman.read_feeds_items = []
        rss_parser_mock_confman.max_article_age = timedelta(days=(100*365))
        mock_confman.cache_path = Mock()
        mock_confman.cache_path.__repr__ = MagicMock(return_value=cache_path)
        mock_confman.cache_path.joinpath = MagicMock(
            return_value=feed_destpath
        )
        ret = download_feed(url)
        ret[0].should.equal(feed_destpath)
        ret[1].should.equal(url)
        feed = Feed(ret)
        feed.is_null.should.be.false
        with open(feed_destpath) as fd:
            fd.read().should.equal(FEED_STR)
        if isfile(feed_destpath):
            remove(feed_destpath)
