# Building OnionShare

Start by getting the source code:

```sh
git clone https://github.com/micahflee/onionshare.git
cd onionshare
```

## Linux

Install the needed dependencies:

For Debian-like distros:

```
apt install -y python3-flask python3-stem python3-pyqt5 python3-crypto python3-socks python-nautilus tor obfs4proxy python3-pytest build-essential fakeroot python3-all python3-stdeb dh-python
```

For Fedora-like distros:

```
dnf install -y python3-flask python3-stem python3-qt5 python3-crypto python3-pysocks nautilus-python tor obfs4 python3-pytest rpm-build
```

After that you can try both the CLI and the GUI version of OnionShare:

```sh
./dev_scripts/onionshare
./dev_scripts/onionshare-gui
```

You can also build OnionShare packages to install:

Create a .deb on Debian-like distros: `./install/build_deb.sh`

Create a .rpm on Fedora-like distros: `./install/build_rpm.sh`

For OpenSuSE: There are instructions for building [in the wiki](https://github.com/micahflee/onionshare/wiki/Linux-Distribution-Support#opensuse-leap-150).

For ArchLinux: There is a PKBUILD available [here](https://aur.archlinux.org/packages/onionshare/) that can be used to install OnionShare.

If you find that these instructions don't work for your Linux distribution or version, consult the [Linux Distribution Support wiki guide](https://github.com/micahflee/onionshare/wiki/Linux-Distribution-Support), which might contain extra instructions.

## Mac OS X

Install Xcode from the Mac App Store. Once it's installed, run it for the first time to set it up. Also, run this to make sure command line tools are installed: `xcode-select --install`. And finally, open Xcode, go to Preferences > Locations, and make sure under Command Line Tools you select an installed version from the dropdown. (This is required for installing Qt5.)

Download and install Python 3.7.2 from https://www.python.org/downloads/release/python-372/. I downloaded `python-3.7.2-macosx10.9.pkg`.

You may also need to run the command `/Applications/Python\ 3.7/Install\ Certificates.command` to update Python 3.6's internal certificate store. Otherwise, you may find that fetching the Tor Browser .dmg file fails later due to a certificate validation error.

Install Qt 5.11.3 from https://www.qt.io/download-open-source/. I downloaded `qt-unified-mac-x64-3.0.6-online.dmg`. In the installer, you can skip making an account, and all you need is `Qt` > `Qt 5.11.3` > `macOS`.

Now install some python dependencies with pip (note, there's issues building a .app if you install this in a virtualenv):

```sh
pip3 install -r install/requirements.txt
```

#### You can run both the CLI and GUI versions of OnionShare without building an bundle

```sh
./dev_scripts/onionshare
./dev_scripts/onionshare-gui
```

#### Building PyInstaller

If you want to build an app bundle, you'll need to use PyInstaller. Recently there has been issues with installing PyInstaller using pip, so here's how to build it from source. First, make sure you don't have PyInstaller currently installed:

```sh
pip3 uninstall PyInstaller
```

Change to a folder where you keep source code, and clone the PyInstaller git repo:

```sh
git clone https://github.com/pyinstaller/pyinstaller.git
```

Verify the v3.4 git tag:

```sh
cd pyinstaller
gpg --keyserver hkps://keyserver.ubuntu.com:443 --recv-key 0xD4AD8B9C167B757C4F08E8777B752811BF773B65
git tag -v v3.4
```

It should say `Good signature from "Hartmut Goebel <h.goebel@goebel-consult.de>`. If it verified successfully, checkout the tag:

```sh
git checkout v3.4
```

And compile the bootloader, following [these instructions](https://pyinstaller.readthedocs.io/en/stable/bootloader-building.html#building-for-mac-os-x). To compile, run this:

```sh
cd bootloader
python3 waf distclean all --target-arch=64bit
```

Finally, install the PyInstaller module into your local site-packages:

```sh
cd ..
python3 setup.py install
```

#### To build the app bundle

```sh
install/build_osx.sh
```

Now you should have `dist/OnionShare.app`.

#### To codesign and build a pkg for distribution

```sh
install/build_osx.sh --release
```

Now you should have `dist/OnionShare.pkg`.

## Windows

### Setting up your dev environment

Download Python 3.7.2, 32-bit (x86) from https://www.python.org/downloads/release/python-372/. I downloaded `python-3.7.2.exe`. When installing it, make sure to check the "Add Python 3.7 to PATH" checkbox on the first page of the installer.

Open a command prompt, cd to the onionshare folder, and install dependencies with pip:

```cmd
pip install -r install\requirements.txt
```

Install the Qt 5.11.3 from https://www.qt.io/download-open-source/. I downloaded `qt-unified-windows-x86-3.0.6-online.exe`. In the installer, you can skip making an account, and all you need `Qt` > `Qt 5.11.3` > `MSVC 2015 32-bit`.

After that you can try both the CLI and the GUI version of OnionShare:

```
python dev_scripts\onionshare
python dev_scripts\onionshare-gui
```

#### If you want to build a .exe

These instructions include adding folders to the path in Windows. To do this, go to Start and type "advanced system settings", and open "View advanced system settings" in the Control Panel. Click Environment Variables. Under "System variables" double-click on Path. From there you can add and remove folders that are available in the PATH.

Download and install the 32-bit [Visual C++ Redistributable for Visual Studio 2015](https://www.microsoft.com/en-US/download/details.aspx?id=48145). I downloaded `vc_redist.x86.exe`.

Download and install 7-Zip from http://www.7-zip.org/download.html. I downloaded `7z1805.exe`.

Download and install the standalone [Windows 10 SDK](https://dev.windows.com/en-us/downloads/windows-10-sdk). Note that you may not need this if you already have Visual Studio.

Add the following directories to the path:

* `C:\Program Files (x86)\Windows Kits\10\bin\10.0.17763.0\x86`
* `C:\Program Files (x86)\Windows Kits\10\Redist\10.0.17763.0\ucrt\DLLs\x86`
* `C:\Users\user\AppData\Local\Programs\Python\Python37-32\Lib\site-packages\PyQt5\Qt\bin`
* `C:\Program Files (x86)\7-Zip`

#### If you want the .exe to not get falsely flagged as malicious by anti-virus software

OnionShare uses PyInstaller to turn the python source code into Windows executable `.exe` file. Apparently, malware developers also use PyInstaller, and some anti-virus vendors have included snippets of PyInstaller code in their virus definitions. To avoid this, you have to compile the Windows PyInstaller bootloader yourself instead of using the pre-compiled one that comes with PyInstaller.

(If you don't care about this, you can install PyInstaller with `pip install PyInstaller==3.4`.)

Here's how to compile the PyInstaller bootloader:

Download and install [Microsoft Build Tools for Visual Studio 2017](https://www.visualstudio.com/downloads/#build-tools-for-visual-studio-2017). I downloaded `vs_buildtools.exe`. In the installer, check the box next to "Visual C++ build tools". Click "Individual components", and under "Compilers, build tools and runtimes", check "Windows Universal CRT SDK". Then click install. When installation is done, you may have to reboot your computer.

Then, enable the 32-bit Visual C++ Toolset on the Command Line like this:

```
cd "C:\Program Files (x86)\Microsoft Visual Studio\2017\BuildTools\VC\Auxiliary\Build"
vcvars32.bat
```

Make sure you have a new enough `setuptools`:

```
pip install setuptools==40.6.3
```

Now make sure you don't have PyInstaller installed from pip:

```
pip uninstall PyInstaller
rmdir C:\Users\user\AppData\Local\Programs\Python\Python37-32\Lib\site-packages\PyInstaller /S
```

Change to a folder where you keep source code, and clone the PyInstaller git repo:

```
git clone https://github.com/pyinstaller/pyinstaller.git
```

To verify the git tag, you first need the signing key's PGP key, which means you need `gpg`. If you installed git from git-scm.com, you can run this from Git Bash:

```
gpg --keyserver hkps://keyserver.ubuntu.com:443 --recv-key 0xD4AD8B9C167B757C4F08E8777B752811BF773B65
```

And now verify the tag:

```
cd pyinstaller
git tag -v v3.4
```

It should say `Good signature from "Hartmut Goebel <h.goebel@goebel-consult.de>`. If it verified successfully, checkout the tag:

```
git checkout v3.4
```

And compile the bootloader, following [these instructions](https://pythonhosted.org/PyInstaller/bootloader-building.html). To compile, run this:

```
cd bootloader
python waf distclean all --target-arch=32bit --msvc_targets=x86
```

Finally, install the PyInstaller module into your local site-packages:

```
cd ..
python setup.py install
```

Now the next time you use PyInstaller to build OnionShare, the `.exe` file should not be flagged as malicious by anti-virus.

#### If you want to build the installer

* Go to http://nsis.sourceforge.net/Download and download the latest NSIS. I downloaded `nsis-3.04-setup.exe`.
* Add `C:\Program Files (x86)\NSIS` to the path.

#### If you want to sign binaries with Authenticode

* You'll need a code signing certificate. I got an open source code signing certificate from [Certum](https://www.certum.eu/certum/cert,offer_en_open_source_cs.xml).
* Once you get a code signing key and certificate and covert it to a pfx file, import it into your certificate store.

### To make a .exe:

* Open a command prompt, cd into the onionshare directory, and type: `pyinstaller install\pyinstaller.spec`. `onionshare-gui.exe` and all of their supporting files will get created inside the `dist` folder.

### To build the installer:

Note that you must have a codesigning certificate installed in order to use the `install\build_exe.bat` script, because it codesigns `onionshare-gui.exe`, `uninstall.exe`, and `onionshare-setup.exe`.

Open a command prompt, cd to the onionshare directory, and type: `install\build_exe.bat`

This will prompt you to codesign three binaries and execute one unsigned binary. When you're done clicking through everything you will have `dist\onionshare-setup.exe`.

## Tests

OnionShare includes PyTest unit tests. To run the tests, first install some dependencies:

```sh
pip3 install -r install/requirements-tests.txt
```

Then you can run `pytest` against the `tests/` directory.

```sh
pytest tests/
```

You can run GUI tests like this:

```sh
pytest --rungui tests/
```

If you would like to also run the GUI unit tests in 'tor' mode, start Tor Browser in the background, then run:

```sh
pytest --rungui --runtor tests/
```

Keep in mind that the Tor tests take a lot longer to run than local mode, but they are also more comprehensive.

You can also choose to wrap the tests in `xvfb-run` so that a ton of OnionShare windows don't pop up on your desktop (you may need to install the `xorg-x11-server-Xvfb` package), like this:

```sh
xvfb-run pytest --rungui tests/
```
