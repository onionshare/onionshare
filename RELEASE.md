# OnionShare Release Process

Unless you're a core OnionShare developer making a release, you'll probably never need to follow it.

## Changelog, version, docs, and signed git tag

Before making a release, you must update the version in these places:

- [ ] `cli/pyproject.toml`
- [ ] `cli/setup.py`
- [ ] `cli/onionshare_cli/resources/version.txt`
- [ ] `desktop/pyproject.toml` (under `version` and the `./onionshare_cli-$VERSION-py3-none-any.whl` dependency)
- [ ] `desktop/src/setup.py`
- [ ] `docs/source/conf.py`

You also must edit these files:

- [ ] `desktop/install/org.onionshare.OnionShare.appdata.xml` should have the correct release date, and links to correct screenshots
- [ ] Update all of the documentation in `docs` to cover new features, including taking new screenshots if necessary.
- [ ] In `snap/snapcraft.yaml`, the `tor`, `libevent`, and `obfs4` parts should be updated if necessary, and all python packages should be updated to match `cli/pyproject.toml` and `desktop/pyproject.toml`
- [ ] `CHANGELOG.md` should be updated to include a list of all major changes since the last release
- [ ] There must be a PGP-signed git tag for the version, e.g. for OnionShare 2.1, the tag must be `v2.1`

The first step for the Linux, macOS, and Windows releases is the same.

Verify the release git tag:

```sh
git fetch
git tag -v v$VERSION
```

If the tag verifies successfully, check it out:

```sh
git checkout v$VERSION
```

## PyPi release

The CLI version of OnionShare gets published on PyPi. To make a release:

```sh
cd cli
poetry install
poetry publish --build
```

## Linux Flatpak release

See instructions for the Flatpak release here: https://github.com/micahflee/org.onionshare.OnionShare

## Linux Snapcraft release

You must have `snap` and `snapcraft` (`snap install snapcraft --classic`) installed.

Build and test the snap before publishing:

```sh
snapcraft
snap install --devmode ./onionshare_*.snap
```

Run the OnionShare snap:

```sh
/snap/bin/onionshare     # GUI version
/snap/bin/onionshare.cli # CLI version
```

## Linux AppImage release

_Note: AppImage packages are currently broken due to [this briefcase bug](https://github.com/beeware/briefcase/issues/504). Until it's fixed, OnionShare for Linux will only be available in Flatpak and Snapcraft._

Build a wheel package for OnionShare CLI:

```sh
cd cli
poetry install
poetry build
```

This will make a file like `dist/onionshare_cli-$VERSION-py3-none-any.whl` (except with your specific version number). Move it into `../desktop/linux`:

```sh
mkdir -p ../desktop/linux
mv dist/onionshare_cli-*-py3-none-any.whl ../desktop/linux
# change back to the desktop directory
cd ../desktop
```

Make sure the virtual environment is active, and then run briefcase create and briefcase build:

```sh
. venv/bin/activate
briefcase create
briefcase build
```

### Windows

Build a wheel package for OnionShare CLI (including Tor binaries, from Tor Browser):

```sh
cd cli
poetry install
poetry build
```

This will make a file like `dist\onionshare_cli-$VERSION-py3-none-any.whl` (except with your specific version number). Move it into `..\desktop`:

```
move dist\onionshare_cli-*-py3-none-any.whl ..\desktop
cd ..\desktop
```

Make sure the virtual environment is active, and then run `briefcase create`:

```sh
venv\Scripts\activate.bat
briefcase create
briefcase package
```

_TODO: Codesign_

### macOS

Build a wheel package for OnionShare CLI (including Tor binaries, from Tor Browser):

```sh
cd cli
poetry install
poetry build
```

This will make a file like `dist\onionshare_cli-$VERSION-py3-none-any.whl` (except with your specific version number). Move it into `..\desktop`:

```
cp dist/onionshare_cli-*-py3-none-any.whl ../desktop
cd ../desktop
```

Make sure the virtual environment is active, and then run `briefcase create`:

```sh
. venv/bin/activate
briefcase create
briefcase package -i "Developer ID Application: Micah Lee"
```
