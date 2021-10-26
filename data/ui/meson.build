glade_conf = configuration_data()
glade_conf.set('PACKAGE_URL', website)
glade_conf.set('DATA_DIR', pkgdatadir)
glade_conf.set('LOCALE_DIR', join_paths(get_option('prefix'), get_option('datadir'), 'locale'))
glade_conf.set('APPID', app_id)
# this is for development version # glade_conf.set('VERSION', ''.join([run_command(['git', 'describe', '--long', '--tags']).stdout(), get_option('profile')]))
glade_conf.set('VERSION', meson.project_version())
glade_conf.set('CONTRIBUTORS', contributors)
glade_conf.set('TRANSLATORS', translators)
glade_conf.set('authorfullname', authorfullname)
glade_conf.set('prettyname', prettyname)

# this has been moved to /data/meson.build
#configure_file(
#    input: 'aboutdialog.glade.in',
#    output: 'aboutdialog.glade',
#    configuration: glade_conf
#)
