#!/usr/bin/env bash

meson setup build --Dprefix="$PWD/build/mprefix" --buildtype=debug --reconfigure
meson compile -C build
meson install -C build
