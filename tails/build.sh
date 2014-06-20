#!/bin/bash

if [[ $EUID -ne 0 ]]; then
    echo "You need to run this as root" 1>&2
    exit 1
fi

PERSISTENT=/home/amnesia/Persistent
INSTALL_DIR=$PERSISTENT/.onionshare_install
ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"

cd $ROOT
rm -rf $INSTALL_DIR &>/dev/null 2>&1
mkdir -p $INSTALL_DIR

# install dependencies
apt-get update
apt-get install -y build-essential fakeroot python-all python-stdeb python-flask python-stem python-qt4
./build_deb.sh

# copy files
cp deb_dist/onionshare_*.deb $INSTALL_DIR
cp /var/cache/apt/archives/libjs-jquery_*.deb $INSTALL_DIR
cp /var/cache/apt/archives/python-flask_*.deb $INSTALL_DIR
cp /var/cache/apt/archives/python-jinja2_*.deb $INSTALL_DIR
cp /var/cache/apt/archives/python-markupsafe_*.deb $INSTALL_DIR
cp /var/cache/apt/archives/python-stem_*.deb $INSTALL_DIR
cp /var/cache/apt/archives/python-werkzeug_*.deb $INSTALL_DIR
cp setup/onionshare80.xpm $INSTALL_DIR
cp tails/install.sh $INSTALL_DIR
cp tails/onionshare-install.desktop $PERSISTENT

# fix permissions
chown -R amnesia:amnesia deb_dist $INSTALL_DIR
chown amnesia:amnesia $PERSISTENT/onionshare-install.desktop
chmod 700 $PERSISTENT/onionshare-install.desktop
