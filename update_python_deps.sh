#!/bin/bash

set -e

rm -rf __venv
virtualenv __venv
source __venv/bin/activate
pip install requirements-parser
flatpak-pip-generator --requirements-file=requirements.txt --output python-deps
mv python-deps.json dist/flatpak/python-deps.json
deactivate
