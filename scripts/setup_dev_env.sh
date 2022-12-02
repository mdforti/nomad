#!/bin/bash

set -e

working_dir=$(pwd)
project_dir=$(dirname $(dirname $(realpath $0)))

cd $project_dir

# Clean up any previous build
rm -rf nomad/app/static/docs
rm -rf nomad/app/static/gui
rm -rf site

# Install nomad
pip install --prefer-binary -r requirements-dev.txt
pip install -e ".[infrastructure,parsing,dev]"

# Build documentation
mkdocs build
mkdir -p nomad/app/static/docs
cp -r site/* nomad/app/static/docs