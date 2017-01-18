# Building OnionShare

Start by getting the source code:

```sh
git clone https://github.com/micahflee/onionshare.git
cd onionshare
```

## Linux

Install the needed dependencies:

For Debian-like distros: `apt install -y build-essential fakeroot python3-all python3-stdeb dh-python  python3-flask python3-stem python3-pyqt5 python-nautilus python3-nose`

For Fedora-like distros: `dnf install -y rpm-build python3-flask python3-stem python3-qt5 nautilus-python`

After that you can try both the CLI and the GUI version of OnionShare:

```sh
./dev_scripts/onionshare
./dev_scripts/onionshare-gui
```

You can also build OnionShare packages to install:

Create a .deb on Debian-like distros: `./install/build_deb.sh`

Create a .rpm on Fedora-like distros: `./install/build_rpm.sh`

For ArchLinux: There is a PKBUILD available [here](https://aur.archlinux.org/packages/onionshare/) that can be used to install OnionShare.

## Mac OS X

Install Xcode from the Mac App Store. Once it's installed, run it for the first time to set it up.

If you don't already have it installed, install [Homebrew](http://brew.sh/).

Install some dependencies using Homebrew:

```sh
brew install python3 pyqt5 qt5
```

Install some dependencies using pip3:

```sh
sudo pip3 install flask stem
```

After that you can try both the CLI and the GUI version of OnionShare:

```sh
./dev_scripts/onionshare
./dev_scripts/onionshare-gui
```

If you want to build a Mac OS X app bundle:

Install the latest development version of cx_Freeze:

* Download a [snapshot](https://bitbucket.org/anthony_tuininga/cx_freeze/downloads) of the latest development version of cx_Freeze, extract it, and cd into the folder you extracted it to
* Build the package: `python3 setup.py bdist_wheel`
* Install it with pip: `sudo pip3 install dist/cx_Freeze-5.0-cp35-cp35m-macosx_10_11_x86_64.whl`

To build the app bundle:

```sh
install/build_osx.sh
```

Now you should have `dist/OnionShare.app`.

To codesign and build a pkg for distribution:

```sh
install/build_osx.sh --release
```

Now you should have `dist/OnionShare.pkg`.

## Windows

### Setting up your dev environment

Download the latest Python 3.6.x, 32-bit (x86) from https://www.python.org/downloads/. I downloaded `python-3.6.0.exe`. When installing it, make sure to check the "Add Python 3.6 to PATH" checkbox on the first page of the installer.

Open a command prompt and install dependencies with pip: `pip install flask stem PyQt5`

Download and install Qt5 from https://www.qt.io/download-open-source/. I downloaded `qt-unified-windows-x86-2.0.4-online.exe`. There's no need to login to a Qt account during installation. Make sure you install the latest Qt 5.x. I installed Qt 5.7.

After that you can try both the CLI and the GUI version of OnionShare:

```
python dev_scripts\onionshare
python dev_scripts\onionshare-gui
```

If you want to build an .exe:

These instructions include adding folders to the path in Windows. To do this, go to Start and type "advanced system settings", and open "View advanced system settings" in the Control Panel. Click Environment Variables. Under "System variables" double-click on Path. From there you can add and remove folders that are available in the PATH.

Download and install the [Microsoft Visual C++ 2008 Redistributable Package (x86)](http://www.microsoft.com/en-us/download/details.aspx?id=29).

Installing cx_Freeze with support for Python 3.5 is annoying. Here are the steps (thanks https://github.com/sekrause/cx_Freeze-Wheels):

* Download and install the Visual C++ Build Tools 2005 from http://go.microsoft.com/fwlink/?LinkId=691126. I downloaded `visualcppbuildtools_full.exe`.
* Install the python wheel package: `pip install wheel`
* Download a [snapshot](https://bitbucket.org/anthony_tuininga/cx_freeze/downloads) of the latest development version of cx_Freeze, extract it, and cd into the folder you extracted it to
* Build the package: `python setup.py bdist_wheel`
* Install it with pip: `pip install dist\cx_Freeze-5.0-cp35-cp35m-win32.whl`

If you want to build the installer:

* Go to http://nsis.sourceforge.net/Download and download the latest NSIS. I downloaded `nsis-3.0-setup.exe`.
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

* Open a command prompt, cd into the onionshare directory, and type: `python setup.py build`. `onionshare.exe`, `onionshare-gui.exe`, and all of their supporting files will get created inside the `build\exe.win32-3.5` folder.

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
