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

Download and install Python 3.8.6 from https://www.python.org/downloads/release/python-386/. I downloaded `python-3.8.6-macosx10.9.pkg`. (You may need to also run `/Applications/Python\ 3.8/Install\ Certificates.command`.)

Install python dependencies:

```sh
pip3 install --user poetry requests
```

Download Tor Browser and extract the binaries:

```sh
./scripts/get-tor-osx.py
```

#### Windows

These instructions include adding folders to the path in Windows. To do this, go to Start and type "advanced system settings", and open "View advanced system settings" in the Control Panel. Click Environment Variables. Under "System variables" double-click on Path. From there you can add and remove folders that are available in the PATH.

Download Python 3.8.6, 32-bit (x86) from https://www.python.org/downloads/release/python-386/. I downloaded `python-3.8.6.exe`. When installing it, make sure to check the "Add Python 3.8 to PATH" checkbox on the first page of the installer.

Download and install 7-Zip from http://www.7-zip.org/download.html. I downloaded `7z1900.exe`. Add `C:\Program Files (x86)\7-Zip` to your path.

Install python dependencies:

```
pip install poetry requests
```

Download Tor Browser and extract the binaries:

```
python scripts\get-tor-windows.py
```

### Prepare the virtual environment

OnionShare uses [Briefcase](https://briefcase.readthedocs.io/en/latest/).

Install Briefcase dependencies by following [these instructions](https://docs.beeware.org/en/latest/tutorial/tutorial-0.html#install-dependencies).

Now create and/or activate a virtual environment.

* Linux and macOS
    ```
    python3 -m venv venv
    . venv/bin/activate
    ```
* Windows
    ```
    python -m venv venv
    venv\Scripts\activate.bat
    ```

While your virtual environment is active, install briefcase from pip.

```
pip install briefcase
```

In order to work with the desktop app, you'll need to build a wheel of the CLI package first, and copy it into the `desktop` folder. You'll need to re-run this script each time you change the CLI code.

```sh
python scripts/rebuild-cli.py
```

### Running OnionShare from the source code tree

Inside the virtual environment, run OnionShare like this to install all of the dependencies:

```
briefcase dev -d
```

Once you have the dependencies installed, you can run it using the `dev.sh` script, which lets you use command line arguments, such as to `--verbose` or `--local-only`:

```
./scripts/dev.sh --help
./scripts/dev.sh -v
./scripts/dev.sh -v --local-only
```

Windows uses `scripts\dev.bat` instead.

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
