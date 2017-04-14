# Building OnionShare

Start by getting the source code:

```sh
git clone https://github.com/micahflee/onionshare.git
cd onionshare
```

## Linux

Install the needed dependencies:

For Debian-like distros: `apt install -y build-essential fakeroot python3-all python3-stdeb dh-python  python3-flask python3-stem python3-pyqt5 python-nautilus python3-nose tor`

For Fedora-like distros: `dnf install -y rpm-build python3-flask python3-stem python3-qt5 nautilus-python tor`

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

Download and install Python 3.5.2 from https://www.python.org/downloads/release/python-352/ (note that a pyinstaller bug prevents you from using Python 3.6). I downloaded `python-3.5.2-macosx10.6.pkg`.

Download and install Qt 5.7.1 for macOS offline installer from https://www.qt.io/download-open-source/. I downloaded `qt-opensource-mac-x64-clang-5.7.1.dmg`. (You can skip making an account in the installer.)

Now install some python dependencies with pip (note, there's issues building a .app if you install this in a virtualenv):

```sh
sudo pip3 install -r install/requirements.txt
```

You can run both the CLI and GUI versions of OnionShare without building an bundle:

```sh
./dev_scripts/onionshare
./dev_scripts/onionshare-gui
```

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

Download the latest Python 3.5.2, 32-bit (x86) from https://www.python.org/downloads/release/python-352/ (note that there's a pyinstaller/pywin32 bug that prevents 3.6.x from working). I downloaded `python-3.5.2.exe`. When installing it, make sure to check the "Add Python 3.5 to PATH" checkbox on the first page of the installer.

Open a command prompt, cd to the onionshare folder, and install dependencies with pip:

```cmd
pip3 install -r install\requirements-windows.txt
```

Download and install Qt5 from https://www.qt.io/download-open-source/. I downloaded `qt-unified-windows-x86-2.0.4-online.exe`. There's no need to login to a Qt account during installation. Make sure you install the latest Qt 5.x. I installed Qt 5.7.

After that you can try both the CLI and the GUI version of OnionShare:

```
python dev_scripts\onionshare
python dev_scripts\onionshare-gui
```

If you want to build a .exe:

These instructions include adding folders to the path in Windows. To do this, go to Start and type "advanced system settings", and open "View advanced system settings" in the Control Panel. Click Environment Variables. Under "System variables" double-click on Path. From there you can add and remove folders that are available in the PATH.

Download and install the 32-bit [Visual C++ Redistributable for Visual Studio 2015](https://www.microsoft.com/en-US/download/details.aspx?id=48145). I downloaded `vc_redist.x86.exe`.

Download and install the standalone [Windows 10 SDK](https://dev.windows.com/en-us/downloads/windows-10-sdk). Note that you may not need this if you already have Visual Studio. Add the following directories to the path:

* `C:\Program Files (x86)\Windows Kits\10\bin\x86`
* `C:\Program Files (x86)\Windows Kits\10\Redist\ucrt\DLLs\x86`
* `C:\Users\user\AppData\Local\Programs\Python\Python35-32\Lib\site-packages\PyQt5\Qt\bin`

If you want to build the installer:

* Go to http://nsis.sourceforge.net/Download and download the latest NSIS. I downloaded `nsis-3.01-setup.exe`.
* Add `C:\Program Files (x86)\NSIS` to the path.

If you want to sign binaries with Authenticode:

* You'll need a code signing certificate. I roughly followed [this guide](http://blog.assarbad.net/20110513/startssl-code-signing-certificate/) to make one using my StartSSL account.
* Once you get a code signing key and certificate and covert it to a pfx file, import it into your certificate store.

### To make a .exe:

For PyInstaller to work, you might need to edit `Scripts\pyinstaller-script.py` in your Python 3.5 folder, to work around [this bug](https://stackoverflow.com/questions/31808180/installing-pyinstaller-via-pip-leads-to-failed-to-create-process) in pip.

* Open a command prompt, cd into the onionshare directory, and type: `pyinstaller install\pyinstaller.spec`. `onionshare-gui.exe` and all of their supporting files will get created inside the `dist` folder.

### To build the installer:

Note that you must have a codesigning certificate installed in order to use the `install\build_exe.bat` script, because it codesigns `onionshare-gui.exe`, `uninstall.exe`, and `OnionShare_Setup.exe`.

Open a command prompt, cd to the onionshare directory, and type: `install\build_exe.bat`

This will prompt you to codesign three binaries and execute one unsigned binary. When you're done clicking through everything you will have `dist\OnionShare_Setup.exe`.

## Tests

OnionShare includes [nose](https://nose.readthedocs.org/en/latest/) unit tests. First, `sudo apt-get install python3-nose` or `sudo pip3 install nose`.

To run the tests:

```sh
nosetests3 test
```
