# OnionShare Release Process

Unless you're a core OnionShare developer making a release, you'll probably never need to follow it.

## Changelog, version, docs, and signed git tag

Before making a release, you must update the version in these places:

- [ ] `cli/pyproject.toml`
- [ ] `cli/setup.py`
- [ ] `cli/onionshare_cli/resources/version.txt`
- [ ] `desktop/pyproject.toml` (under `version` and **don't forget** the `./onionshare_cli-$VERSION-py3-none-any.whl` dependency)
- [ ] `desktop/src/setup.py`
- [ ] `docs/source/conf.py` (`version` at the top, and the `versions` list too)
- [ ] `snap/snapcraft.yaml`

If you update `flask-socketio`, ensure that you also update the [socket.io.min.js](https://github.com/micahflee/onionshare/blob/develop/cli/onionshare_cli/resources/static/js/socket.io.min.js) file to a version that is [supported](https://flask-socketio.readthedocs.io/en/latest/#version-compatibility) by the updated version of `flask-socketio`.

Use tor binaries from the latest Tor Browser:

- [ ] `desktop/scripts/get-tor-osx.py`
- [ ] `desktop/scripts/get-tor-windows.py`

Update the documentation:

- [ ] Update all of the documentation in `docs` to cover new features, including taking new screenshots if necessary

Finalize localization:

- [ ] Merge all the translations from weblate
- [ ] In `docs` run `poetry run ./check-weblate.py [API_KEY]` to see which translations are >90% in the app and docs
- [ ] Edit `cli/onionshare_cli/settings.py`, make sure `self.available_locales` lists only locales that are >90% translated
- [ ] Edit `docs/source/conf.py`, make sure `languages` lists only languages that are >90% translated
- [ ] Edit `docs/build.sh` and make sure `LOCALES=` lists the same languages as above, in `docs/source/conf.py`
- [ ] Make sure the latest documentation is built and committed:
  ```
  cd docs
  poetry install
  poetry run ./build.sh
  ```

You also must edit these files:

- [ ] `desktop/src/org.onionshare.OnionShare.appdata.xml` should have the correct version, release date, and links to correct screenshots
- [ ] `CHANGELOG.md` should be updated to include a list of all major changes since the last release

Make sure snapcraft packaging works. In `snap/snapcraft.yaml`:

- [ ] The `tor`, `libevent`, and `obfs4` parts should be updated if necessary
- [ ] All python packages should be updated to match `cli/pyproject.toml` and `desktop/pyproject.toml`
- [ ] Test the snap package, ensure it works

Finally:

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

## Linux Snapcraft release

You must have `snap` and `snapcraft` (`snap install snapcraft --classic`) installed.

Build and test the snap before publishing:

```sh
snapcraft
snap install --devmode ./onionshare_$VERSION_amd64.snap
```

This will create `onionshare_$VERSION_amd64.snap`.

Run the OnionShare snap locally:

```sh
/snap/bin/onionshare     # desktop version
/snap/bin/onionshare.cli # CLI version
```

Upload the to Snapcraft:

```sh
snapcraft login
snapcraft upload --release=stable onionshare_$VERSION_amd64.snap
```

## Linux AppImage release

_Note: AppImage packages are currently broken due to [this briefcase bug](https://github.com/beeware/briefcase/issues/504). Until it's fixed, OnionShare for Linux will only be available in Flatpak and Snapcraft._

Set up the development environment described in `README.md`.

Make sure your virtual environment is active:

```sh
. venv/bin/activate
```

Run the AppImage build script:

```sh
./package/linux/build-appimage.py
```

## Windows

Set up the development environment described in `README.md`. And install the [Windows 10 SDK](https://developer.microsoft.com/en-us/windows/downloads/windows-10-sdk) and add `C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x86` to your path.

Make sure your virtual environment is active:

```
venv\Scripts\activate.bat
```

Run the Windows build script:

```
python package\windows\build.py
```

This will create `desktop/windows/OnionShare-$VERSION.msi`, signed.

## macOS

Set up the development environment described in `README.md`. And install `create-dmg`:

```sh
brew install create-dmg
```

Make sure your virtual environment is active:

```sh
. venv/bin/activate
```

Run the macOS build script:

```sh
./package/macos/build.py --with-codesign
```

Now, notarize the release. You must have an app-specific Apple ID password saved in the login keychain called `onionshare-notarize`.

- Notarize it: `xcrun altool --notarize-app --primary-bundle-id "com.micahflee.onionshare" -u "micah@micahflee.com" -p "@keychain:onionshare-notarize" --file macOS/OnionShare.dmg`
- Wait for it to get approved, check status with: `xcrun altool --notarization-history 0 -u "micah@micahflee.com" -p "@keychain:onionshare-notarize"`
- After it's approved, staple the ticket: `xcrun stapler staple macOS/OnionShare.dmg`

This will create `desktop/macOS/OnionShare.dmg`, signed and notarized.

## Source package

To make a source package, run `./build-source.sh $TAG`, where `$TAG` is the the name of the signed git tag, e.g. `v2.1`.

This will create `dist/onionshare-$VERSION.tar.gz`.

## Publishing the release

### PGP signatures

After following all of the previous steps, gather these files:

- `onionshare_$VERSION_amd64.snap`
- `OnionShare-$VERSION.msi`
- `OnionShare.dmg` (rename it to `OnionShare-$VERSION.dmg`)
- `onionshare-$VERSION.tar.gz`

Create a PGP signature for each of these files, e.g:

```sh
gpg -a --detach-sign OnionShare-$VERSION.tar.gz
gpg -a --detach-sign [... and so on]
```

### Create a release on GitHub:

- Match it to the version tag, put the changelog in description of the release
- Upload all 8 files (binary and source packages and their `.asc` signatures)

### Update onionshare-cli on PyPi

```sh
cd cli
poetry install
poetry publish --build
```

### Update Flathub

After there's a new release tag, make the Flathub package work here: https://github.com/flathub/org.onionshare.OnionShare

You must have `flatpak` and `flatpak-builder` installed, with flathub remote added (`flatpak remote-add --if-not-exists --user flathub https://flathub.org/repo/flathub.flatpakrepo`).

- [ ] Change the tag (for both `onionshare` and `onionshare-cli`) to match the new git tag
- [ ] Update `tor`, `libevent`, and `obfs4` dependencies, if necessary
- [ ] Built the latest python dependencies using [this tool](https://github.com/flatpak/flatpak-builder-tools/blob/master/pip/flatpak-pip-generator) (see below)
- [ ] Test the Flatpak package, ensure it works

```
# you may need to install toml
pip3 install --user toml

# clone flatpak-build-tools
git clone https://github.com/flatpak/flatpak-builder-tools.git

# get onionshare-cli dependencies
cd poetry
./flatpak-poetry-generator.py ../../onionshare/cli/poetry.lock
cd ..

# get onionshare dependencies
cd pip
./flatpak-pip-generator $(python3 -c 'import toml; print("\n".join(toml.loads(open("../../onionshare/desktop/pyproject.toml").read())["tool"]["briefcase"]["app"]["onionshare"]["requires"]))' |grep -v "./onionshare_cli" |grep -v -i "pyside2" |tr "\n" " ")
mv python3-modules.json onionshare.json

# use something like https://www.json2yaml.com/ to convert to yaml and update the manifest
# add all of the modules in both onionshare-cli and onionshare to the submodules of "onionshare"
# - poetry/generated-poetry-sources.json (onionshare-cli)
# - pip/python3-modules.json (onionshare)
```

Build and test the Flatpak package before publishing:

```sh
flatpak-builder build --force-clean --install-deps-from=flathub --install --user org.onionshare.OnionShare.yaml
flatpak run org.onionshare.OnionShare
```

Create a [single-file bundle](https://docs.flatpak.org/en/latest/single-file-bundles.html):

```sh
flatpak build-bundle ~/.local/share/flatpak/repo OnionShare-$VERSION.flatpak org.onionshare.OnionShare --runtime-repo=https://flathub.org/repo/flathub.flatpakrepo
```

Create a PGP signature for the flatpak single-file bundle:

```sh
gpg -a --detach-sign OnionShare-$VERSION.flatpak
```

Upload this `.flatpak` and its sig to the GitHub release as well.

### Update Homebrew

- Make a PR to [homebrew-cask](https://github.com/homebrew/homebrew-cask) to update the macOS version

### Update onionshare.org

- Upload all 10 files to https://onionshare.org/dist/$VERSION/
- Update the [onionshare-website](https://github.com/micahflee/onionshare-website) repo:
  - Edit `latest-version.txt` to match the latest version
  - Update the version number and download links
  - Deploy to https://onionshare.org/

### Update docs.onionshare.org

- Upload everything from `docs/build/docs` to https://docs.onionshare.org/

### Update the community

- Upload all 10 files to the OnionShare team Keybase filesystem
- Email the [onionshare-dev](https://lists.riseup.net/www/subscribe/onionshare-dev) mailing list announcing the release
- Blog, tweet, toot, etc.
