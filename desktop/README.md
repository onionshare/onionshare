# OnionShare Desktop

## Building OnionShare

Start by getting the source code and changing to the `desktop` folder:

```sh
git clone https://github.com/onionshare/onionshare.git
cd onionshare/desktop
```

Make sure you have Python 3 installed. If you're using Windows or macOS, install version 3.9.9 [from python.org](https://www.python.org/downloads/release/python-399/). For Windows, make sure to install the 32-bit (x86) version, and to check the box to add python to the path on the first page of the installer.

Make sure you have [poetry installed](https://python-poetry.org/docs/#installation), and then install the dependencies:

```sh
poetry install
```

### Install platform-specific dependencies

#### Linux

In Ubuntu 20.04 you need the `libxcb-xinerama0` package installed.

Download Tor Browser and extract the binaries:

```sh
poetry run ./scripts/get-tor-linux.py
```

#### macOS

Download Tor Browser and extract the binaries:

```sh
poetry run ./scripts/get-tor-osx.py
```

#### Windows

These instructions include adding folders to the path in Windows. To do this, go to Start and type "advanced system settings", and open "View advanced system settings" in the Control Panel. Click Environment Variables. Under "System variables" double-click on Path. From there you can add and remove folders that are available in the PATH.

Download and install 7-Zip from https://7-zip.org/download.html. I downloaded `7z1900.exe`. Add `C:\Program Files (x86)\7-Zip` to your path.

Download Tor Browser and extract the binaries:

```sh
poetry run python scripts\get-tor-windows.py
```

### Compile dependencies

Install Go. The simplest way to make sure everything works is to install Go by following [these instructions](https://golang.org/doc/install). (In Windows, make sure to install the 32-bit version of Go, such as `go1.17.5.windows-386.msi`.)

Download and compile `meek-client`:

```sh
./scripts/build-meek-client.py
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
