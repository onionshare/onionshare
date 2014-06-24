# Building OnionShare

## GNU/Linux

Start by getting a copy of the source code:

```sh
git clone https://github.com/micahflee/onionshare.git
cd onionshare
```

*For .deb-based distros (like Debian, Ubuntu, Linux Mint):*

Note that python-stem appears in Debian wheezy and newer (so by extension Tails 1.1 and newer), and it appears in Ubuntu 13.10 and newer. Older versions of Debian and Ubuntu aren't supported.

```sh
sudo apt-get install -y build-essential fakeroot python-all python-stdeb python-flask python-stem python-qt4
./build_deb.sh
sudo dpkg -i deb_dist/onionshare_*.deb
```

*For .rpm-based distros (Red Hat, Fedora, CentOS):*

```sh
sudo yum install -y rpm-build python-flask python-stem pyqt4
./build_rpm.sh
sudo yum install -y dist/onionshare-*.rpm
```

## Mac OS X

To install the right dependencies, you need homebrew and pip installed on your Mac. Follow instructions at http://brew.sh/ to install homebrew, and run `sudo easy_install pip` to install pip.

The first time you're setting up your dev environment:

```sh
git clone https://github.com/micahflee/onionshare.git
cd onionshare
echo export PYTHONPATH=\$PYTHONPATH:/usr/local/lib/python2.7/site-packages/ >> ~/.profile
source ~/.profile
brew install qt4 pyqt
sudo pip install virtualenv
virtualenv env
. env/bin/activate
pip install flask stem py2app
# fixes a silly bug https://bitbucket.org/ronaldoussoren/py2app/issue/143/resulting-app-mistakenly-looks-for-pyside
patch env/lib/python2.7/site-packages/py2app/util.py < setup/py2app.patch
```

Each time you start work:

```sh
. env/bin/activate
```

Build the .app:

```sh
python setup.py py2app
```

Now you should have `dist/OnionShare.app`.

## Windows

The first time you're setting up your dev environment:

* Download and install the latest python 2.7 from https://www.python.org/downloads/ -- make sure you install the 32-bit version.
* Right click on Computer, go to Properties. Click "Advanced system settings". Click Environment Variables. Under "System variables" double-click on Path to edit it. Add `;C:\Python27;C:\Python27\Scripts` to the end. Now you can just type `python` to run python scripts in the command prompt.
* Go to https://pip.pypa.io/en/latest/installing.html. Right-click on `get-pip.py` and Save Link As, and save it to your home folder.
* Open `cmd.exe` as an administrator. Type: `python get-pip.py`. Now you can use `pip` to install packages.
* Go to http://www.riverbankcomputing.com/software/pyqt/download and download the latest PyQt4 for Windows for python 2.7, 32-bit (I downloaded `PyQt4-4.11-gpl-Py2.7-Qt4.8.6-x32.exe`), then install it.
* Go to http://www.py2exe.org/ and download the latest py2exe for python 2.7, 32-bit (I downloaded `py2exe-0.6.9.win32-py2.7.exe`), then install it.
* Open a command prompt and type: `pip install flask stem`
* Go to `C:\Python27\Lib\site-packages\flask\` and delete the folder `testsuite`. This is necessary to work around a py2exe bug.

To make an exe:

* Open a command prompt, cd to the onionshare folder, and type: `python setup.py py2exe`. This will create a ton of files in `dist`, including `onionshare.exe`.

## Tests

OnionShare includes [nose](https://nose.readthedocs.org/en/latest/) unit tests. First,

```sh
sudo pip install nose
```

To run the tests:

```sh
nosetests test
```
