from typing import Tuple
from gettext import gettext as _
import readability
import pygments
import pygments.lexers
from lxml.html import (
    fromstring as html_fromstring,
    tostring as html_tostring,
    HtmlElement
)
from pygments.formatters import HtmlFormatter
from gfeeds.reader_mode_style import CSS, DARK_MODE_CSS


# Thanks to Eloi Rivard (azmeuk) for the contribution on the media block
def _build_media_text(title: str, content: str) -> str:
    return '''
        <p>
            <strong>{0}:</strong>
            {1}
        </p>'''.format(title, content.replace("\n", "<br />"))


def _build_media_link(title: str, content: str, link: str):
    return _build_media_text(
        title, f'<a href="{link}">{content}</a>'
    )


# thumbnails aren't supposed to be links, images can be?
# funnily enough, using `#` as a link opens the main content url
# that's because the webkitview sets the base url to the feed item link
def _build_media_img(title, imgurl, link='#') -> str:
    return _build_media_link(
        title, f'<br /><img src="{imgurl}" />', link
    )


def build_syntax_highlight(root: HtmlElement) -> Tuple[str, HtmlElement]:
    syntax_highlight_css = ''
    code_nodes = root.xpath(
        '//pre/code'
    )
    lexer = None
    for code_node in code_nodes:
        classes = code_node.attrib.get('class', '').split(' ')
        for klass in classes:
            try:
                lexer = pygments.lexers.get_lexer_by_name(
                    klass.replace('language-', ''),
                    stripall=True,
                )
                break
            except pygments.util.ClassNotFound:
                pass

        if not code_node.text:
            continue

        if not lexer:
            try:
                lexer = pygments.lexers.guess_lexer(code_node.text)
            except pygments.util.ClassNotFound:
                continue

        formatter = HtmlFormatter(style='solarized-dark')

        if not syntax_highlight_css:
            syntax_highlight_css = formatter.get_style_defs()

        newtext = pygments.highlight(code_node.text, lexer, formatter)
        newhtml = html_fromstring(newtext)

        pre_node = code_node.getparent()
        pre_node.getparent().replace(pre_node, newhtml)

    return syntax_highlight_css, root


def build_syntax_highlight_from_raw_html(raw_html) -> Tuple[str, HtmlElement]:
    return build_syntax_highlight(
        html_fromstring(
            raw_html if type(raw_html) == str else raw_html.decode()
        )
    )


def build_reader_html(og_html, dark_mode: bool = False, fp_item=None) -> str:
    def build_media_block():
        if not fp_item:
            return ''
        media_s = '<hr />'
        for el in fp_item:
            if el[:6].lower() == 'media_':
                try:
                    if el.lower() == 'media_thumbnail':
                        media_s += _build_media_img(
                            _('Thumbnail'),
                            fp_item["media_thumbnail"][0]["url"]
                        )
                    else:
                        for subel in fp_item[el]:
                            media_s += _build_media_text(
                                subel.capitalize(),
                                fp_item[el][subel]
                            )
                except Exception:
                    continue
        return media_s if media_s != '<hr />' else ''

    doc = readability.Document(og_html)
    content = doc.summary(True)
    syntax_highlight_css, root = build_syntax_highlight_from_raw_html(content)
    content = html_tostring(
        root, encoding='utf-8'
    ).decode().replace(
        '</p><a ', '<a '
    ).replace(
        '</a><p>', '</a>'
    ).replace(
        '</p><em>', '<em>'
    ).replace(
        '</em><p>', '</em>'
    )
    content += build_media_block()
    return f'''<html>
        <head>
            <meta charset="UTF-8">
            <style>
                {CSS}
                {DARK_MODE_CSS if dark_mode else ""}
                {syntax_highlight_css}
            </style>
            <title>{doc.short_title()}</title>
        </head>
        <body>
            <article>
                <h1>{doc.short_title() or fp_item["title"]}</h1>
                {content}
            </article>
        </body>
    </html>'''
