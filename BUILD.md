# Building OnionShare

## GNU/Linux

Start by getting a copy of the source code:

    git clone https://github.com/micahflee/onionshare.git
    cd onionshare

*For .deb-based distros (like Debian, Ubuntu, Linux Mint):*

Note that python-stem appears in Debian wheezy and newer (so by extension Tails 1.1 and newer), and it appears in Ubuntu 13.10 and newer. Older versions of Debian and Ubuntu aren't supported.

    sudo apt-get install -y build-essential fakeroot python-all python-stdeb python-flask python-stem python-webkit
    ./build_deb.sh
    sudo dpkg -i deb_dist/onionshare_*.deb

*For .rpm-based distros (Red Hat, Fedora, CentOS):*

    sudo yum install -y rpm-build python-flask python-stem pywebkitgtk
    ./build_rpm.sh
    sudo yum install -y dist/onionshare-*.rpm

## Mac OS X

*Note: This is a work-in-progress. The OnionShare GUI doesn't yet work in Mac OS X. See https://github.com/micahflee/onionshare/issues/43 for progress.*

Get a copy of the source code:

    git clone https://github.com/micahflee/onionshare.git
    cd onionshare

Install py2app (if you don't have pip installed, you can `sudo easy_install pip`):

    sudo pip install py2app

Then build the .app:

    python setup.py py2app

Now you'll see `dist/OnionShare.app` with a nice icon. However, it won't run yet.

## Windows

*Note: Haven't started figuring this out yet.*

