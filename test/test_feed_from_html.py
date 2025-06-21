from pathlib import Path
from rilato.util.download_manager import extract_feed_url_from_html

__HTML_BASE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title></title>
    <link rel="alternate" type="{0}" href="{1}">
</head>
<body>
    <h1>Foo bar</h1>
    <p>Lorem ipsum dolor sit amet, qui minim labore adipisicing
    minim sint cillum sint consectetur cupidatat.</p>
</body>
</html>
"""


def __mock(monkeypatch, html: str):
    def mock_download_raw(link: str, dest: str) -> None:
        with open(dest, "w") as fd:
            fd.write(html)

    monkeypatch.setattr("rilato.util.download_manager.download_raw", mock_download_raw)

    class MockConfManager:
        def __init__(self):
            self.cache_path = Path("/tmp/org.gabmus.rilato.test/cache")

    monkeypatch.setattr("rilato.confManager.ConfManager", MockConfManager)


def test_rss_https(monkeypatch):
    __mock(
        monkeypatch,
        __HTML_BASE.format(
            "application/rss+xml", "https://fake0.example.com/blog/rss.xml"
        ),
    )
    res = extract_feed_url_from_html("https://fake0.example.com/blog")
    assert res == "https://fake0.example.com/blog/rss.xml"


def test_rss_abspath(monkeypatch):
    __mock(monkeypatch, __HTML_BASE.format("application/rss+xml", "/blog/rss.xml"))
    res = extract_feed_url_from_html("https://fake1.example.com/blog")
    assert res == "https://fake1.example.com/blog/rss.xml"


def test_rss_abspath_different_dir(monkeypatch):
    __mock(monkeypatch, __HTML_BASE.format("application/rss+xml", "/another/rss.xml"))
    res = extract_feed_url_from_html("https://fake2.example.com/blog")
    assert res == "https://fake2.example.com/another/rss.xml"


def test_rss_relpath(monkeypatch):
    __mock(monkeypatch, __HTML_BASE.format("application/rss+xml", "rss.xml"))
    res = extract_feed_url_from_html("https://fake3.example.com/blog")
    assert res == "https://fake3.example.com/blog/rss.xml"


def test_rss_relpath_trailing_slash(monkeypatch):
    __mock(monkeypatch, __HTML_BASE.format("application/rss+xml", "rss.xml"))
    res = extract_feed_url_from_html("https://fake4.example.com/blog/")
    assert res == "https://fake4.example.com/blog/rss.xml"


def test_fail(monkeypatch):
    __mock(
        monkeypatch,
        __HTML_BASE.replace('<link rel="alternate" type="{0}" href="{1}">', ""),
    )
    res = extract_feed_url_from_html("https://fake5.example.com/blog")
    assert res is None
