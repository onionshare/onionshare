#!/bin/bash

# This script pushes updates to my Ubuntu PPA: https://launchpad.net/~micahflee/+archive/ppa
# If you want to use it, you'll need your own ~/.dput.cf and ssh key.
# More info: https://help.launchpad.net/Packaging/PPA/Uploading

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
cd $DIR

VERSION=`cat resources/version.txt`

rm -rf deb_dist >/dev/null 2>&1
python3 setup.py --command-packages=stdeb.command sdist_dsc
cd deb_dist/onionshare-$VERSION
dpkg-buildpackage -S
cd ..
dput ppa:micahflee/ppa onionshare_$VERSION-1_source.changes
cd ..
