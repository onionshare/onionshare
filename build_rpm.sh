#!/bin/sh

VERSION=`cat version`

# clean up from last build
rm -r build dist

# build binary package
python setup.py bdist_rpm --requires="python-flask, python-stem, pywebkitgtk"

# install it
echo ""
echo "To install, run:"
echo "sudo yum install dist/onionshare-$VERSION-1.noarch.rpm"
