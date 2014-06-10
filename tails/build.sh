#!/bin/bash

if [[ $EUID -ne 0 ]]; then
    echo "You need to run this as root" 1>&2
    exit 1
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
cd $DIR

# install dependencies
apt-get update
apt-get install -y build-essential fakeroot python-all python-stdeb python-flask python-stem python-webkit
./build_deb.sh

# copy .deb files
rm tails/*.deb
cp deb_dist/onionshare_*.deb tails
cp /var/cache/apt/archives/libjs-jquery_*.deb tails
cp /var/cache/apt/archives/python-flask_*.deb tails
cp /var/cache/apt/archives/python-jinja2_*.deb tails
cp /var/cache/apt/archives/python-markupsafe_*.deb tails
cp /var/cache/apt/archives/python-stem_*.deb tails
cp /var/cache/apt/archives/python-werkzeug_*.deb tails

# fix permissions
chown -R amnesia:amnesia deb_dist tails/*.deb
