# OnionShare Desktop

## Building OnionShare

Start by getting the source code and changing to the `desktop` folder:

```sh
git clone https://github.com/onionshare/onionshare.git
cd onionshare/desktop
```

Make sure you have Python 3 installed. If you're using Windows or macOS, install version 3.9.13 [from python.org](https://www.python.org/downloads/release/python-3913/). For Windows, make sure to check the box to add python to the path on the first page of the installer.

Make sure you have [poetry](https://python-poetry.org/) installed:

```
pip3 install poetry
```

And install the poetry dependencies:

```sh
poetry install
```

**Windows users:** You may need to install [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/), making sure to check "Desktop development with C++", before `poetry install` will work properly.

### Get Tor

**Linux users:** In Ubuntu 20.04 you need the `libxcb-xinerama0` package installed.

**Windows users:** Download and install 7-Zip from https://7-zip.org/download.html. [Add](https://medium.com/@kevinmarkvi/how-to-add-executables-to-your-path-in-windows-5ffa4ce61a53) `C:\Program Files (x86)\7-Zip` to your path.

Download Tor Browser and extract the binaries for your platform. The platform must be `win32`, `win64`, `macos`, or `linux64`.

```sh
poetry run python ./scripts/get-tor.py [platform]
```

### Compile dependencies

Install Go. The simplest way to make sure everything works is to install Go by following [these instructions](https://golang.org/doc/install).

Compile pluggable transports:

**Windows users, in PowerShell:**

```powershell
.\scripts\build-pt-obfs4proxy.ps1
.\scripts\build-pt-snowflake.ps1
.\scripts\build-pt-meek.ps1
```

**macOS and Linux users:**

```sh
./scripts/build-pt-obfs4proxy.sh
./scripts/build-pt-snowflake.sh
./scripts/build-pt-meek.sh
```

### Running OnionShare from the source code tree

To run OnionShare from the source tree:

```sh
poetry run onionshare
poetry run onionshare --help
poetry run onionshare -v
poetry run onionshare -v --local-only
```

You can also run `onionshare-cli` from the source tree, and it will look for Tor binaries in `desktop/onionshare/resources/tor`.

```sh
poetry run onionshare-cli --help
```

## Running tests

Run the tests:

```sh
poetry run ./tests/run.sh
```

If you want to run tests while hiding the GUI, you must have the `xvfb` package installed, and then:

```sh
xvfb-run poetry run ./tests/run.sh
```
