# Building OnionShare

## GNU/Linux

Start by getting a copy of the source code:

    git clone https://github.com/micahflee/onionshare.git
    cd onionshare

*For .deb-based distros (like Debian, Ubuntu, Linux Mint):*

Note that python-stem appears in Debian wheezy and newer (so by extension Tails 1.1 and newer), and it appears in Ubuntu 13.10 and newer. Older versions of Debian and Ubuntu aren't supported.

    sudo apt-get install -y build-essential fakeroot python-all python-stdeb python-flask python-stem python-qt4
    ./build_deb.sh
    sudo dpkg -i deb_dist/onionshare_*.deb

*For .rpm-based distros (Red Hat, Fedora, CentOS):*

    sudo yum install -y rpm-build python-flask python-stem pyqt4
    ./build_rpm.sh
    sudo yum install -y dist/onionshare-*.rpm

## Mac OS X

The first time you're setting up your dev environment:

    echo export PYTHONPATH=\$PYTHONPATH:/usr/local/lib/python2.7/site-packages/ >> ~/.profile
    source ~/.profile
    brew install qt4 pyqt
    virtualenv env
    . env/bin/activate
    pip install flask stem py2app
    # fixes a silly bug https://bitbucket.org/ronaldoussoren/py2app/issue/143/resulting-app-mistakenly-looks-for-pyside
    patch env/lib/python2.7/site-packages/py2app/util.py < setup/py2app.patch

Each time you start work:

    . env/bin/activate

Build the .app:

    python setup.py py2app

Now you should have `dist/OnionShare.app`.

## Windows

*Coming soon.*

