from gfeeds.confManager import ConfManager
from gi.repository import Gio

confman = ConfManager()

sans_font = 'Cantarell'  # confman.sans_font
serif_font = 'DejaVu Serif'  # confman.serif_font
mono_font = 'DejaVu Sans Mono'  # confman.mono_font

CSS = f'''@font-face {{
  font-family: ephy-reader-serif;
  src: local('{serif_font}');
  font-weight: normal;
  font-style: normal;
  font-display: block;
}}

@font-face {{
  font-family: ephy-reader-serif;
  src: local('{serif_font} Italic');
  font-weight: normal;
  font-style: italic;
  font-display: block;
}}

@font-face {{
  font-family: ephy-reader-serif;
  src:local('{serif_font} Bold');
  font-weight: bold;
  font-style: normal;
  font-display: block;
}}

@font-face {{
  font-family: ephy-reader-serif;
  src:local('{serif_font} Bold Italic');
  font-weight: bold;
  font-style: italic;
  font-display: block;
}}

@font-face {{
  font-family: ephy-reader-sans;
  src: local('{sans_font}');
  font-weight: normal;
  font-style: normal;
  font-display: block;
}}

@font-face {{
  font-family: ephy-reader-sans;
  src: local('{sans_font} Italic');
  font-weight: normal;
  font-style: italic;
  font-display: block;
}}

@font-face {{
  font-family: ephy-reader-sans;
  src: local('{sans_font} Bold');
  font-weight: bold;
  font-style: normal;
  font-display: block;
}}

@font-face {{
  font-family: ephy-reader-sans;
  src: local('{sans_font} Bold Italic');
  font-weight: bold;
  font-style: italic;
  font-display: block;
}}

@font-face {{
  font-family: ephy-reader-mono;
  src: local('{mono_font}');
  font-weight: normal;
  font-style: normal;
  font-display: block;
}}

@font-face {{
  font-family: ephy-reader-mono;
  src: local('{mono_font} Italic');
  font-weight: normal;
  font-style: italic;
  font-display: block;
}}

@font-face {{
  font-family: ephy-reader-mono;
  src: local('{mono_font} Bold');
  font-weight: bold;
  font-style: normal;
  font-display: block;
}}

@font-face {{
  font-family: ephy-reader-mono;
  src: local('{mono_font} Bold Italic');
  font-weight: bold;
  font-style: italic;
  font-display: block;
}}
''' + Gio.resources_lookup_data(
    '/org/gabmus/gfeeds/ui/reader_mode_style.css',
    Gio.ResourceLookupFlags.NONE
).get_data().decode()
DARK_MODE_CSS = Gio.resources_lookup_data(
    '/org/gabmus/gfeeds/ui/reader_mode_dark_style.css',
    Gio.ResourceLookupFlags.NONE
).get_data().decode()
