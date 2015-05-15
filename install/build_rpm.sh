#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
cd $DIR

VERSION=`cat version`

# clean up from last build
rm -r build dist >/dev/null 2>&1

# build binary package
python setup.py bdist_rpm --requires="python-flask, python-stem, pyqt4"

# install it
echo ""
echo "To install, run:"
echo "sudo yum install dist/onionshare-$VERSION-1.noarch.rpm"
