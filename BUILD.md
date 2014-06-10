# Building OnionShare

## GNU/Linux

Start by getting a copy of the source code:

    git clone https://github.com/micahflee/onionshare.git
    cd onionshare

*For .deb-based distros (like Debian, Ubuntu, Linux Mint):*

    sudo apt-get install -y python-all python-stdeb python-flask python-stem python-webkit
    ./build_deb.sh
    sudo dpkg -i deb_dist/onionshare_*.deb

*For .rpm-based distros (Red Hat, Fedora, CentOS):*

    sudo yum install -y rpm-build python-flask python-stem pywebkitgtk
    ./build_rpm.sh
    sudo yum install -y dist/onionshare-*.rpm

## Mac OS X

*Note: These instructions are a work-in-progress. The OnionShare GUI doesn't yet work in Mac OS X.*

If you don't already have pip installed, install it like this:

    sudo easy_install pip

Then use pip to install py2app:

    sudo pip install py2app

## Windows

*Note: Haven't started figuring this out yet.*
