#!/bin/bash

if [[ $EUID -ne 0 ]]; then
    echo "You need to run this as root" 1>&2
    exit 1
fi

PERSISTENT=/home/amnesia/Persistent
INSTALL_DIR=$PERSISTENT/.onionshare_install

dpkg -i $INSTALL_DIR/*.deb

/usr/bin/sudo -u amnesia /usr/bin/notify-send "OnionShare Installed" "Open with Applications > Internet > OnionShare"
