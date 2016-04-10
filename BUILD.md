# Building OnionShare

## GNU/Linux

Start by getting a copy of the source code:

```sh
git clone https://github.com/micahflee/onionshare.git
cd onionshare
```

*For .deb-based distros (like Debian, Ubuntu, Linux Mint):*

Note that python3-stem appears in Debian wheezy and newer, and it appears in Ubuntu 13.10 and newer. Older versions of Debian and Ubuntu aren't supported.

```sh
sudo apt-get install -y build-essential fakeroot python3-all python3-stdeb python3-flask python3-stem python3-pyqt5 dh-python
./install/build_deb.sh
sudo dpkg -i deb_dist/onionshare_*.deb
```
Note that OnionShare uses stdeb to generate Debian packages, and `python3-stdeb` is not available in Ubuntu 14.04 (Trusty). Because of this, you can't use the `build_install.sh` script to build the .deb file in versions of Ubuntu 14.04 and earlier. However, .deb files you build in later versions of Ubuntu will install and work fine in 14.04.

*For .rpm-based distros (Red Hat, Fedora, CentOS):*

```sh
sudo sudo dnf install -y rpm-build python3-flask python3-stem python3-qt5
./install/build_rpm.sh
sudo yum install -y dist/onionshare-*.rpm
```

Depending on your distribution, you may need to use `yum` instead of `dnf`.

*For ArchLinux:*

There is a PKBUILD available [here](https://aur.archlinux.org/packages/onionshare/) that can be used to install OnionShare.

## Mac OS X

Install Xcode from the Mac App Store. Once it's installed, run it for the first time to set it up.

If you don't already have it installed, install [Homebrew](http://brew.sh/).

Install some dependencies using Homebrew:

```sh
brew install python3 pyqt5 qt5
```

Install some dependencies using pip3:

```sh
sudo pip3 install pyinstaller flask stem
```

Get the source code:

```sh
git clone https://github.com/micahflee/onionshare.git
cd onionshare
```

To build the .app:

```sh
install/build_osx.sh
```

Now you should have `dist/OnionShare.app`.

To codesign and build a .pkg for distribution:

```sh
install/build_osx.sh --sign
```

Now you should have `dist/OnionShare.pkg`.

## Windows

### Setting up your dev environment

These instructions include adding folders to the path in Windows. To do this, go to Start and type "advanced system settings", and open "View advanced system settings" in the Control Panel. Click Environment Variables. Under "System variables" double-click on Path. From there you can add and remove folders that are available in the PATH.

First, download and install the 32-bit (x86) version of Python 3.4.x from https://www.python.org/downloads/windows/. You need 3.4 instead of 3.5 because PyQt5 was built with 3.4. Add `C:\Python34` and `C:\Python34\Scripts` to the path.

Open a command prompt and install some dependencies with pip: `pip install flask stem py2exe`

Download and install Qt5 from https://www.qt.io/download-open-source/. I downloaded `qt-unified-windows-x86-2.0.2-2-online.exe`. There's no need to login to a Qt account during installation. Make sure you install the latest Qt 5.x.

Download and install the latest PyQt5 for 32-bit Windows from https://www.riverbankcomputing.com/software/pyqt/download5. I downloaded `PyQt5-5.5.1-gpl-Py3.4-Qt5.5.1-x32.exe`.

Download and install the latest 32-bit pywin32 binary for Python 3.4 from http://sourceforge.net/projects/pywin32/. I downloaded `pywin32-220.win32-py3.4.exe`.

Download and install the [Microsoft Visual C++ 2008 Redistributable Package (x86)](http://www.microsoft.com/en-us/download/details.aspx?id=29).

If you want to build the installer:

* Go to http://nsis.sourceforge.net/Download and download the latest NSIS. I downloaded `nsis-3.0b0-setup.exe`.
* Add `C:\Program Files (x86)\NSIS` to the path.

If you want to sign binaries with Authenticode:

* You'll need a code signing certificate. I roughly followed [this guide](http://blog.assarbad.net/20110513/startssl-code-signing-certificate/) to make one using my StartSSL account.
* Once you get a code signing key and certificate and covert it to a pfx file, import it into your certificate store.
* Windows 7:
  * Go to http://msdn.microsoft.com/en-us/vstudio/aa496123 and install the latest .NET Framework. I installed `.NET Framework 4.6`.
  * Go to http://www.microsoft.com/en-us/download/confirmation.aspx?id=8279 and install the Windows SDK.
  * Add `C:\Program Files\Microsoft SDKs\Windows\v7.1\Bin` to the path.
* Windows 10:
  * Go to https://dev.windows.com/en-us/downloads/windows-10-sdk and install the standalone Windows 10 SDK. Note that you may not need this if you already have Visual Studio.
  * Add `C:\Program Files (x86)\Windows Kits\10\bin\x86` to the path.

### To make a .exe:

* Open a command prompt, cd into the onionshare directory, and type: `python setup.py py2exe`. `onionshare.exe` and all of its supporting files will get created inside the `dist` folder.

### To build the installer:

Note that you must have a codesigning certificate installed in order to use the `install\build_exe.bat` script, because it codesigns `onionshare.exe`, `uninstall.exe`, and `OnionShare_Setup.exe`.

Open a command prompt, cd to the onionshare directory, and type: `install\build_exe.bat`

This will prompt you to codesign three binaries and execute one unsigned binary. When you're done clicking through everything you will have `dist\OnionShare_Setup.exe`.

## Tests

OnionShare includes [nose](https://nose.readthedocs.org/en/latest/) unit tests. First, `sudo apt-get install python3-nose` or `sudo pip3 install nose`.

To run the tests:

```sh
nosetests3 test
```
