# <a href="https://gabmus.gitlab.io/gnome-feeds"><img height="32" src="data/icons/org.gabmus.gfeeds.svg" /> Feeds</a>

An RSS/Atom feed reader for GNOME.

![screenshot](https://gitlab.gnome.org/World/gfeeds/-/raw/website/static/screenshots/mainwindow.png)

[![Download on Flathub](https://raw.githubusercontent.com/flatpak-design-team/flathub-mockups/master/assets/download-button/download.svg?sanitize=true)](https://flathub.org/apps/details/org.gabmus.gfeeds)

## Dependencies

- python 3.9
- Gtk4
- [libadwaita](https://gitlab.gnome.org/GNOME/libadwaita)
- [python-syndom](https://gitlab.com/gabmus/syndication-domination)
- [python-readability-lxml](https://github.com/buriy/python-readability)
- [python-pygments](https://github.com/pygments/pygments)
- [python-pillow](https://github.com/python-pillow/Pillow)
- [python-beautifulsoup4](https://pypi.org/project/beautifulsoup4/)
- [python-humanize](https://github.com/jmoiron/humanize)
- [python-requests](https://github.com/psf/requests)
- [python-html5lib](https://github.com/html5lib/html5lib-python)

## Build and run from source

**Note**: If you're looking to install the app for regular use, [download it from Flathub](https://flathub.org/apps/details/org.gabmus.gfeeds) or from your distribution repositories. These instructions are only for developers and package maintainers.

```bash
git clone https://gitlab.gnome.org/World/gfeeds
cd gfeeds
mkdir build
cd build
meson .. -Dprefix="$PWD/build/mprefix"
ninja
ninja install
ninja run
```

## Hacking

You might want to check your code with [flake8](https://github.com/pycqa/flake8) before opening a merge request.

```bash
flake8 gfeeds
```
