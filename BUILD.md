# Building OnionShare

For GNU/Linux and OSX, get a copy of the source code:

    git clone https://github.com/micahflee/onionshare.git
    cd onionshare

## Debian-based GNU/Linux

## Red Hat-based GNU/Linux

Install dependencies and build the RPM:

    sudo yum install -y rpm-build python-flask python-stem pywebkitgtk
    ./build_rpm.sh

The RPM will end up in your dist folder. You can install it like this:

    sudo yum install -y dist/onionshare-*.rpm

## Mac OS X

*Note: These instructions are a work-in-progress. The OnionShare GUI doesn't yet work in Mac OS X.*

If you don't already have pip installed, install it like this:

    sudo easy_install pip

Then use pip to install py2app:

    sudo pip install py2app


