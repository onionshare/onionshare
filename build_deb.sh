#!/bin/sh

VERSION=`cat version`

# clean up from last build
rm -r deb_dist

# build binary package
python setup.py --command-packages=stdeb.command bdist_deb

# install it
echo ""
echo "To install, run:"
echo "sudo dpkg -i deb_dist/onionshare_$VERSION-1_all.deb"
