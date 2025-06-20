# rilato

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A description of this project.

## Development

### Install Dependencies

**System packages**
```bash
# Debian/Ubuntu
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 ninja-build meson python3-pip
# Fedora
sudo dnf install python3-gobject python3-cairo gobject-introspection-devel gtk4-devel libadwaita-devel meson ninja-build python3-pip
```

**Python & project**
```bash
pip3 install poetry
poetry install
```

### Build & Run
```bash
poetry run rilato-build
poetry run rilato
