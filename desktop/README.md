# OnionShare Desktop

## Building OnionShare

### Install platform-specific dependencies

#### Linux

If you're using Linux, install `tor` and `obfs4proxy` from either the [official Debian repository](https://support.torproject.org/apt/tor-deb-repo/), or from your package manager.

Then download Qt 5.14.0 for Linux:

```sh
cd ~/Downloads
wget https://download.qt.io/official_releases/qt/5.14/5.14.0/qt-opensource-linux-x64-5.14.0.run
```

If you'd like to check to make sure you have the exact installer I have, here is the sha256 checksum:

```sh
sha256sum qt-opensource-linux-x64-5.14.0.run
4379f147c6793ec7e7349d2f9ee7d53b8ab6ea4e4edf8ee0574a75586a6a6e0e  qt-opensource-linux-x64-5.14.0.run
```

Then make it executable and install Qt:

```sh
chmod +x qt-opensource-linux-x64-5.14.0.run
./qt-opensource-linux-x64-5.14.0.run
```

You have to create a Qt account and login to install Qt. Choose the default installation folder in your home directory. The only component you need is `Qt 5.14.0` > `Desktop gcc 64-bit`.

#### macOS

#### Windows

### Prepare the code

Get the source code and change to the `desktop` folder:

```sh
git clone https://github.com/micahflee/onionshare.git
cd onionshare/desktop
```

OnionShare uses [Briefcase](https://briefcase.readthedocs.io/en/latest/).

Install Briefcase dependencies by following [these instructions](https://docs.beeware.org/en/latest/tutorial/tutorial-0.html#install-dependencies).

Now create and/or activate a virtual environment.

```
python3 -m venv venv
. venv/bin/activate
```

While your virtual environment is active, install briefcase from pip.

```
pip install briefcase
```

Run OnionShare from the source tree like this:

```
briefcase dev
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

## Making a release