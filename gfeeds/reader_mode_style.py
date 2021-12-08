from gfeeds.confManager import ConfManager
from gi.repository import Gio, Gtk

settings = Gtk.Settings.get_default()
confman = ConfManager()


def get_gtk_font():
    ss = settings.get_property('gtk-font-name').split(' ')
    ss.pop(-1)
    return ' '.join(ss).strip()


def get_css():
    gtk_font = get_gtk_font()
    sans_font = gtk_font
    serif_font = gtk_font
    mono_font = confman.conf['font_monospace_custom']
    if not confman.conf['font_use_system_for_titles']:
        serif_font = confman.conf['font_titles_custom']
    if not confman.conf['font_use_system_for_paragraphs']:
        sans_font = confman.conf['font_paragraphs_custom']
    css = ''
    for typ, var in zip(
            ('sans',   'serif',     'mono'),
            (sans_font, serif_font, mono_font)
    ):
        for variant, weight, style in zip(
                ('',       ' Italic', ' Bold',  ' Bold Italic'),
                ('normal', 'normal',  'bold',   'bold'),
                ('normal', 'italic',  'normal', 'italic')
        ):
            css += f'''
            @font-face {{
                font-family: gfeeds-reader-{typ};
                src: local('{var}{variant}');
                font-weight: {weight};
                font-style: {style};
                font-display: block;
            }}'''
    css += Gio.resources_lookup_data(
        '/org/gabmus/gfeeds/ui/reader_mode_style.css',
        Gio.ResourceLookupFlags.NONE
    ).get_data().decode()
    return css
