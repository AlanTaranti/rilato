from gettext import gettext
from typing import List, Tuple, Union
from rilato.feed_item import FeedItem
from rilato.util.readability_wrapper import RDoc
import pygments
import pygments.lexers
from lxml.html import (
    fromstring as html_fromstring,
    tostring as html_tostring,
    HtmlElement,
)
from pygments.formatters import HtmlFormatter
from rilato.util.reader_mode_style import get_css


# Thanks to Eloi Rivard (azmeuk) for the contribution on the media block
def _build_media_text(title: str, content: str) -> str:
    return """
        <p>
            <strong>{0}:</strong>
            {1}
        </p>""".format(title, content.replace("\n", "<br />"))


def _build_media_link(title: str, content: str, link: str):
    return _build_media_text(title, f'<a href="{link}">{content}</a>')


# thumbnails aren't supposed to be links, images can be?
# funnily enough, using `#` as a link opens the main content url
# that's because the webkitview sets the base url to the feed item link
def _build_media_img(title, imgurl, link="#") -> str:
    return _build_media_link(title, f'<br /><img src="{imgurl}" />', link)


def build_syntax_highlight(root: HtmlElement) -> Tuple[str, HtmlElement]:
    syntax_highlight_css = ""
    code_nodes: List[HtmlElement] = root.xpath("//pre/code")
    lexer = None
    for code_node in code_nodes:
        classes = code_node.attrib.get("class", "").split(" ")
        for klass in classes:
            try:
                lexer = pygments.lexers.get_lexer_by_name(
                    klass.replace("language-", ""),
                    stripall=True,
                )
                break
            except pygments.util.ClassNotFound:
                pass

        code_text = code_node.text_content()
        if not code_text:
            continue

        if lexer is None:
            try:
                lexer = pygments.lexers.guess_lexer(code_text)
            except pygments.util.ClassNotFound:
                continue

        formatter = HtmlFormatter(style="solarized-dark", linenos=False)

        if not syntax_highlight_css:
            syntax_highlight_css = formatter.get_style_defs()

        newtext = pygments.highlight(code_text, lexer, formatter)
        newhtml = html_fromstring(newtext)

        pre_node = code_node.getparent()
        pre_node.getparent().replace(pre_node, newhtml)

    return syntax_highlight_css, root


def build_syntax_highlight_from_raw_html(
    raw_html: Union[str, bytes],
) -> Tuple[str, HtmlElement]:
    return build_syntax_highlight(
        html_fromstring(raw_html if isinstance(raw_html, str) else raw_html.decode())
    )


def build_reader_html(og_html, feed_item: FeedItem, dark_mode: bool = False) -> str:
    doc = RDoc(og_html)
    content = doc.summary(html_partial=True)
    syntax_highlight_css, root = build_syntax_highlight_from_raw_html(content)
    content = html_tostring(root, encoding="utf-8")
    author_html = ""
    if feed_item.author_name:
        if feed_item.author_url:
            author_html = gettext('Author: <a href="{0}">{1}</a>').format(
                feed_item.author_url, feed_item.author_name
            )
        else:
            author_html = gettext("Author: {0}".format(feed_item.author_name))
    if not isinstance(content, str):
        content = content.decode()
    return f"""<html>
        <head>
            <meta charset="UTF-8" />
            <style>
                {get_css()}
                {syntax_highlight_css}
            </style>
            <title>{doc.short_title() or feed_item.title}</title>
        </head>
        <body {'class="dark"' if dark_mode else ""} dir=auto>
            <article>
                <h1>{doc.short_title() or feed_item.title}</h1>
                <p>{author_html}</p>
                {
        f'<img src="{feed_item.image_url}" /> <hr />'
        if feed_item.image_url and feed_item.image_url not in content
        else ""
    }
                {content}
            </article>
        </body>
    </html>"""
