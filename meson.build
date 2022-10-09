project('gfeeds',
    version: '2.0.0',
    meson_version: '>= 0.58.0',
    license: 'GPL3'
)

description = 'News reader for GNOME'
prettyname = 'Feeds'
prettylicense = 'GPL-3.0+'

author = 'gabmus'
authorfullname = 'Gabriele Musco'
authoremail = 'emaildigabry@gmail.com'
domain = 'org'
# app_id built as: domain.author.project_name
gitrepo = 'https://gitlab.com/'+author+'/'+meson.project_name()
website = 'http://'+meson.project_name()+'.'+author+'.org'

# NOTE: if you contributed, feel free to add your name and email address here
contributors = '\n'.join([
    'Gabriele Musco (GabMus) &lt;emaildigabry@gmail.com&gt;',
    'Adrien Plazas (aplazas) &lt;kekun.plazas@laposte.net&gt;',
    'Christopher Davis (BrainBlasted) &lt;brainblasted@disroot.org&gt;',
    'Ivan Kupalov (charlag) &lt;charlag@tuta.io&gt;',
    'Ignacio Losiggio (iglosiggio) &lt;iglosiggio@dc.uba.ar&gt;',
    'Éloi Rivard (azmeuk)'
])

message('Looking for dependencies')
dependency('glib-2.0')
dependency('gobject-introspection-1.0', version: '>=1.35.9')
dependency('gtk4', version :'>=4.3.1')
dependency('libadwaita-1', version :'>=1.2.alpha')

i18n = import('i18n')
python = import('python')
py_installation = python.find_installation('python3')
if not py_installation.found()
    error('No valid python3 binary found')
endif
gnome = import('gnome')
prefix = get_option('prefix')  # should be /usr
bindir = get_option('bindir')  # should be bin
datadir = get_option('datadir')  # should be /usr/share
pkgdatadir = join_paths(prefix, datadir, meson.project_name())
pythondir = py_installation.get_install_dir()
localedir = join_paths(prefix, get_option('localedir'))

install_subdir(meson.project_name(), install_dir: pythondir)
subdir('data')
subdir('bin')
subdir('po')

# tests

pytest_exe = find_program('pytest', required: false)
if pytest_exe.found()
    test(
        'pytest',
        pytest_exe,
        args: [meson.project_source_root() + '/test'],
        suite: 'pytest',
        env: [
            'GSETTINGS_SCHEMA_DIR="@0@:${GSETTINGS_SCHEMA_DIR}"'.format(
                join_paths(datadir, 'glib-2.0/schemas')
            )
        ]
    )
endif

gnome.post_install(
  glib_compile_schemas: true,
  gtk_update_icon_cache: true
)
