project('ovh.technenotes.myapp')

source_path = meson.source_root()
conf = configuration_data()
conf.set('CINSTPATH', source_path / 'src')

# Configure GSettings
schemas_dir = get_option('prefix') / get_option('datadir') / 'glib-2.0' / 'schemas'
settings_schemas = [ 'data/ovh.technenotes.myapp.gschema.xml' ]
install_data(settings_schemas, install_dir: schemas_dir)
meson.add_install_script('glib-compile-schemas', schemas_dir)

# Install config files
install_data(['data/markdown-extra-tech.lang'], install_dir : get_option('prefix') / get_option('datadir') / 'gtksourceview-3.0/language-specs')
install_data('data/codezone-tech.xml', install_dir : get_option('prefix') / get_option('datadir') / 'gtksourceview-3.0/styles')

# Install font files
install_data('data/Lato-Regular.ttf', install_dir : get_option('prefix') / get_option('datadir') / 'fonts')

# Setup .desktop file and icon
configure_file(
  input: 'data/technenotes.desktop',
  output: 'technenotes.desktop',
  configuration: conf,
  install: true,
  install_dir: get_option('prefix') / get_option('datadir') / 'applications'
)



