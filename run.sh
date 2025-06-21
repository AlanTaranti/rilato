#!/bin/bash

export GSETTINGS_SCHEMA_DIR="$PWD/build/build/testdir/share/glib-2.0/schemas"
ninja -C build
ninja -C build install

./build/build/testdir/bin/rilato
