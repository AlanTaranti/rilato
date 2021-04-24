# <a href="https://gabmus.gitlab.io/gnome-feeds"><img height="32" src="data/icons/org.gabmus.gfeeds.svg" /> Feeds</a>

An RSS/Atom feed reader for GNOME.

![screenshot](https://gitlab.gnome.org/World/gfeeds/raw/website/website/screenshots/mainwindow.png)

## Notes on the distribution of this app

I decided to target flatpak mainly. It's just another package manager at the end of the day, but
it's supported by many Linux distributions. It bundles all of the dependencies you need in one
package.

This helps a lot in supporting many different distros because I know which version of which
dependency you have installed, so I don't have to mess with issues caused by version mismatches.
If you want to report an issue, feel free to. But please at least first see if this issue happens
with the flatpak version as well.

As for development it's a similar story. I do most of my testing directly inside a flatpak sandbox
and you should do the same. It's easy to set up, just open up this repo in GNOME Builder and press
the run button. It will handle the rest.

## Installing from Flathub

You can install Feeds via [Flatpak](https://flathub.org/apps/details/org.gabmus.gfeeds).

## Installing from AUR

Feeds is available as an AUR package: [`gfeeds-git`](https://aur.archlinux.org/packages/gfeeds-git/).

## Installing from Fedora

Feeds is available in [Fedora repos](https://apps.fedoraproject.org/packages/gnome-feeds): `sudo dnf install gnome-feeds`

# Building on different distributions

**Note**: these are illustrative instructions. If you're a developer or a package maintainer, they
can be useful to you. If not, just install the flatpak.

## Building on Ubuntu/Debian

```bash
sudo apt-get install python-html5lib webkit2gtk python-lxml python-requests python-bs4
sudo pip install listparser 

git clone https://gitlab.gnome.org/World/gfeeds
cd gfeeds
mkdir build
cd build
meson ..
meson configure -Dprefix=$PWD/testdir # use this line if you want to avoid installing system wide
ninja
ninja install
```

## Building on Arch/Manjaro

```bash
sudo pacman -S python-html5lib webkit2gtk python-lxml python-requests python-pip python-gobject python-feedparser python-beautifulsoup4
yay -S python-listparser python-readability-lxml

git clone https://gitlab.gnome.org/GabMus/gfeeds
cd gfeeds
mkdir build
cd build
meson ..
meson configure -Dprefix=$PWD/testdir # use this line if you want to avoid installing system wide
ninja
ninja install
```

## Building on Fedora

```bash
sudo dnf install appstream python3-html5lib webkit2gtk3 python3-lxml python3-requests python3-pip python3-feedparser python3-beautifulsoup4
sudo pip install listparser

git clone https://gitlab.gnome.org/World/gfeeds
cd gfeeds
mkdir build
cd build
meson ..
meson configure -Dprefix=$PWD/testdir # use this line if you want to avoid installing system wide
ninja
ninja install
```
