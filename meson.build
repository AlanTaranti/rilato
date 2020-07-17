project('gfeeds',
    version: '0.14',
    meson_version: '>= 0.50.0',
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

translators = '\n'.join([
    'Polish: Michał Nowakowski &lt;nowakowski@offshore.rocks&gt;',
    'German: Onno Giesmann (Etamuk) &lt;nutzer3105@gmail.com&gt;',
    'Russian: Alessandra Gallia &lt;alessandragalliaaru@gmail.com&gt;',
    'Brazilian Portoguese: Gleisson Joaquim (gleissonjoaquim3) &lt;gleisscg2@gmail.com&gt;',
    'Spanish: Juan Campos (juan.campos) &lt;juan.camposzambrana@gmail.com&gt;',
    'Italian: Gabriele Musco (GabMus) &lt;emaildigabry@gmail.com&gt;'
])

i18n = import('i18n')
python = import('python3')
gnome = import('gnome')
prefix = get_option('prefix') # should be /usr
bindir = get_option('bindir') # should be bin
datadir = get_option('datadir') # should be /usr/share
pkgdatadir = join_paths(prefix, datadir, meson.project_name())
pythondir = join_paths(prefix, python.sysconfig_path('purelib'))
localedir = join_paths(prefix, get_option('localedir'))

install_subdir('gfeeds', install_dir: pythondir)
subdir('data')
subdir('bin')
subdir('po')

meson.add_install_script('meson_post_install.py')

# envdata = environment()
# python_paths = [join_paths(meson.current_build_dir(), '..')]
# envdata.append('PYTHONPATH', python_paths)
# envdata.append('TESTS_BUILDDIR', meson.current_build_dir())
# test(
#   'unit-tests',
#   import('python').find_installation('python3'),
#   args: ['-m', 'unittest', 'tests'],
#   env: envdata
# )
