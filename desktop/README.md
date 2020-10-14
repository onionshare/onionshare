# OnionShare Desktop

## Building OnionShare

### Install platform-specific dependencies

#### Linux

If you're using Linux, install `tor` and `obfs4proxy` from either the [official Debian repository](https://support.torproject.org/apt/tor-deb-repo/), or from your package manager.

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