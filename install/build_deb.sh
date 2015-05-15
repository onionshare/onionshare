#!/bin/sh

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
cd $DIR

VERSION=`cat version`

# clean up from last build
rm -r deb_dist >/dev/null 2>&1

# build binary package
python setup.py --command-packages=stdeb.command bdist_deb

# install it
echo ""
echo "To install, run:"
echo "sudo dpkg -i deb_dist/onionshare_$VERSION-1_all.deb"
