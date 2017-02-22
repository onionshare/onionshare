#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
cd $DIR

VERSION=`cat share/version.txt`

# clean up from last build
rm -r build dist >/dev/null 2>&1

# build binary package
python3 setup.py bdist_rpm --requires="python3-flask, python3-stem, python3-qt5, nautilus-python"

# install it
echo ""
echo "To install, run:"
echo "sudo dnf install dist/onionshare-$VERSION-1.noarch.rpm"
