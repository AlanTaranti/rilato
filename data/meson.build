desktop_file = i18n.merge_file(
        input: 'me.alantaranti.rilato.desktop.in',
       output: 'me.alantaranti.rilato.desktop',
         type: 'desktop',
       po_dir: '../po',
      install: true,
  install_dir: get_option('datadir') / 'applications'
)

desktop_utils = find_program('desktop-file-validate', required: false)
if desktop_utils.found()
  test('Validate desktop file', desktop_utils, args: [desktop_file])
endif

appstream_file = i18n.merge_file(
        input: 'me.alantaranti.rilato.metainfo.xml.in',
       output: 'me.alantaranti.rilato.metainfo.xml',
       po_dir: '../po',
      install: true,
  install_dir: get_option('datadir') / 'metainfo'
)

appstreamcli = find_program('appstreamcli', required: false, disabler: true)
test('Validate appstream file', appstreamcli,
     args: ['validate', '--no-net', '--explain', appstream_file])

install_data('me.alantaranti.rilato.gschema.xml',
  install_dir: get_option('datadir') / 'glib-2.0' / 'schemas'
)

subdir('ui')

service_conf = configuration_data()
service_conf.set('bindir', get_option('prefix') / get_option('bindir'))
configure_file(
  input: 'me.alantaranti.rilato.service.in',
  output: 'me.alantaranti.rilato.service',
  configuration: service_conf,
  install_dir: get_option('datadir') / 'dbus-1' / 'services'
)

subdir('icons')
