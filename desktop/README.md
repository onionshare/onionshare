# OnionShare Desktop

## Building OnionShare

Start by getting the source code and changing to the `desktop` folder:

```sh
git clone https://github.com/micahflee/onionshare.git
cd onionshare/desktop
```

### Install platform-specific dependencies

#### Linux

If you're using Linux, install `tor` and `obfs4proxy` from either the [official Debian repository](https://support.torproject.org/apt/tor-deb-repo/), or from your package manager.

#### macOS

#### Windows

These instructions include adding folders to the path in Windows. To do this, go to Start and type "advanced system settings", and open "View advanced system settings" in the Control Panel. Click Environment Variables. Under "System variables" double-click on Path. From there you can add and remove folders that are available in the PATH.

Download Python 3.8.6, 32-bit (x86) from https://www.python.org/downloads/release/python-386/. I downloaded `python-3.8.6.exe`. When installing it, make sure to check the "Add Python 3.8 to PATH" checkbox on the first page of the installer.

Download and install 7-Zip from http://www.7-zip.org/download.html. I downloaded `7z1900.exe`. Add `C:\Program Files (x86)\7-Zip` to your path.

Install dependencies:

```
pip install requests
```

Download Tor Browser and extract the binaries by running:

```
cd ..\cli
python scripts\get-tor-windows.py
```

### Prepare the code

OnionShare uses [Briefcase](https://briefcase.readthedocs.io/en/latest/).

Install Briefcase dependencies by following [these instructions](https://docs.beeware.org/en/latest/tutorial/tutorial-0.html#install-dependencies).

Now create and/or activate a virtual environment.

```
python3 -m venv venv
. venv/bin/activate
```

Or in Windows:

```
python -m venv venv
venv\Scripts\activate.bat
```

While your virtual environment is active, install briefcase from pip.

```
pip install briefcase
```

Run OnionShare from the source tree like this:

```
briefcase dev -d
```

## Running tests

Install these packages inside your virtual environment:

```sh
pip install pytest pytest-briefcase pytest-faulthandler pytest-qt
```

Then run the tests:

```sh
./tests/run.sh
```

If you want to run tests while hiding the GUI, you must have the `xvfb` package installed, and then:

```sh
xvfb-run ./tests/run.sh
```

## Making a release

First, build a wheel package for OnionShare CLI:

```sh
cd onionshare/cli
poetry install
poetry build
```

This will make a file like `dist/onionshare_cli-$VERSION-py3-none-any.whl` (except with your specific version number). Move it into `../desktop/linux`:

```
mkdir -p ../desktop/linux
mv dist/onionshare_cli-*-py3-none-any.whl ../desktop/linux
# change back to the desktop directory
cd ../desktop
```

Make sure the virtual environment is active, and then run `briefcase create` and `briefcase build`:

```sh
. venv/bin/activate
briefcase create
briefcase build
```