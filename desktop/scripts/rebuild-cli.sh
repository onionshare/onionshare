#!/bin/bash

# Build the CLI python wheel and copy it to the desktop folder

SCRIPTS_DIR="$( cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd )"
cd $SCRIPTS_DIR
cd ../../cli
poetry install
poetry build
cp dist/*.whl ../desktop