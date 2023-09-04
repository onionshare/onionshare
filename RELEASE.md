# OnionShare Release Process

Unless you're a core OnionShare developer making a release, you'll probably never need to follow it.

## Preparing the release

### Update the version in these places

- [ ] `cli/pyproject.toml`
- [ ] `cli/onionshare_cli/resources/version.txt`
- [ ] `desktop/pyproject.toml`
- [ ] `desktop/setup.py`
- [ ] `desktop/org.onionshare.OnionShare.appdata.xml`
- [ ] `docs/source/conf.py` (`version` at the top, and the `versions` list too)
- [ ] `snap/snapcraft.yaml`

### You also must edit these files

- [ ] `desktop/org.onionshare.OnionShare.appdata.xml` should have the correct release date, and links to correct screenshots
- [ ] `CHANGELOG.md` should be updated to include a list of all major changes since the last release

### Update dependencies

#### Python dependencies

Check `cli/pyproject.toml` to see if any hard-coded versions should be updated. Then, update the dependencies like this:

```sh
cd cli
poetry update
cd ..
```

If you update `flask-socketio`, ensure that you also update the [socket.io.min.js](https://github.com/micahflee/onionshare/blob/develop/cli/onionshare_cli/resources/static/js/socket.io.min.js) file to a version that is [supported](https://flask-socketio.readthedocs.io/en/latest/#version-compatibility) by the updated version of `flask-socketio`.

Check `desktop/pyproject.toml` to see if any hard-coded versions should be updated. Then, update the dependencies like this:

```
cd desktop
poetry update
cd ..
```

Update the docs dependencies like this:

```
cd docs
poetry update
cd ..
```

#### Tor and pluggable transports

- [ ] Update the version of `meek`, `obfs4proxy`, and `snowflake` in the `desktop/scripts/build-pt-*` scripts, both the bash and PowerShell scripts.


### Update the documentation

- [ ] Update all of the documentation in `docs` to cover new features, including taking new screenshots if necessary

### Finalize localization

- [ ] Merge all the translations from weblate
- [ ] In `docs` run `poetry run ./check-weblate.py [API_KEY]` to see which translations are >90% in the app and docs
- [ ] Edit `cli/onionshare_cli/settings.py`, make sure `self.available_locales` lists only locales that are >90% translated
- [ ] From the `desktop` folder in the virtual env, run `./scripts/countries-update-list.py` to make sure the localized country list for censorship circumvention is available in all available languages
- [ ] Edit `docs/source/conf.py`, make sure `languages` lists only languages that are >90% translated
- [ ] Edit `docs/build.sh` and make sure `LOCALES=` lists the same languages as above, in `docs/source/conf.py`
- [ ] Make sure the latest documentation is built and committed:
  ```
  cd docs
  poetry install
  poetry run ./build.sh
  ```

### Make sure Snapcraft packaging works

In `snap/snapcraft.yaml`:

- [ ] The `tor`, `libevent`, `obfs4`, `snowflake-client`, and `meek-client` parts should be updated if necessary
- [ ] In the `onionshare` part, in the `override-pull` section, all of the dependencies in the `requirements.txt` file should match the dependencies listed in `cli/pyproject.toml` and `desktop/pyproject.toml`, with the exception of PySide2
- [ ] With every commit to the `main` branch, Snapcraft's CI should trigger builds. Make sure the builds all succeeded at https://snapcraft.io/onionshare/builds (you must be logged in), and test them. You can install them with: `snap install onionshare --edge`

### Make sure the Flatpak packaging works

In `flatpak/org.onionshare.OnionShare.yaml`:

- [ ] Update `tor`, `libevent`, `obfs4`, `meek-client`, and `snowflake-client` dependencies, if necessary
- [ ] Built the latest python dependencies using [this tool](https://github.com/flatpak/flatpak-builder-tools/blob/master/pip/flatpak-pip-generator) (see below)
- [ ] Test the Flatpak package, ensure it works

```
pip3 install toml requirements-parser

# clone flatpak-build-tools
git clone https://github.com/flatpak/flatpak-builder-tools.git

# get onionshare-cli dependencies
cd poetry
./flatpak-poetry-generator.py ../../onionshare/cli/poetry.lock
cd ..

# get onionshare dependencies
cd pip
./flatpak-pip-generator $(python3 -c 'import toml; print("\n".join(toml.loads(open("../../onionshare/desktop/pyproject.toml").read())["tool"]["poetry"]["dependencies"]))' |grep -vi onionshare_cli |grep -vi python | grep -vi pyside6 | grep -vi cx_freeze |tr "\n" " ")
cd ..

# convert to yaml
./flatpak-json2yaml.py -o onionshare-cli.yml poetry/generated-poetry-sources.json
./flatpak-json2yaml.py -o onionshare.yml pip/python3-modules.json
```

Now, merge `onionshare-cli.yml` and `onionshare.yml` into the Flatpak manifest.

Build and test the Flatpak package before publishing:

```sh
flatpak-builder build --force-clean --install-deps-from=flathub --install --user org.onionshare.OnionShare.yaml
flatpak run org.onionshare.OnionShare
```

### Create a signed git tag

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

## Making the release

### Linux Snapcraft release

From https://snapcraft.io/onionshare/releases (you must be logged in), promote the release from latest/edge to latest/beta, then latest/candidate, then latest/stable.

### Linux Flatpak release

- [ ] Create a new branch in https://github.com/flathub/org.onionshare.OnionShare for the version
- [ ] Overwrite the manifest in the flathub repo with the updated version in [flatpak/org.onionshare.OnionShare.yaml](./flatpak/org.onionshare.OnionShare.yaml)
- [ ] Edit it so that the sources for `onionshare` and `onionshare-cli` are the GitHub repo, with the correct git tag, rather than the local filesystem
- [ ] Make a PR in the flathub repo, and merge it to make a release

### Windows release

Set up the packaging environment:

- Install the Windows SDK from here: https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/ and add `C:\Program Files (x86)\Microsoft SDKs\ClickOnce\SignTool` to the path (you'll need it for `signtool.exe`)
- Go to https://dotnet.microsoft.com/download/dotnet-framework and download and install .NET Framework 3.5 SP1 Runtime. I downloaded `dotnetfx35.exe`.
- Go to https://wixtoolset.org/releases/ and download and install WiX toolset. I downloaded `wix311.exe`. Add `C:\Program Files (x86)\WiX Toolset v3.11\bin` to the path.

Github Actions will build the binaries. Find the Github Actions `build` workflow, switch to the summary tab, and download:

- `build-win32`
- `build-win64`

Extract these files, change to the `desktop` folder, and run:

```
poetry run python .\scripts\build-windows.py codesign [onionshare_win32_path] [onionshare_win64_path]
poetry run python .\scripts\build-windows.py package [onionshare_win32_path] [onionshare_win64_path]
```

This will create:

- `desktop/dist/OnionShare-win32-$VERSION.msi`
- `desktop/dist/OnionShare-win64-$VERSION.msi`

### macOS release

In order to make a universal2 binary, you must run this one a Mac with Apple Silicon. To keep a clean environment, you can use VM.

Set up the VM like this:

- Install [Homebrew](https://brew.sh/)
- `brew install create-dmg libiodbc`
- Install the latest Python 3.10 from https://www.python.org/downloads/
- Install ARM64 version of Go from https://go.dev/dl/
- Install "Postgres.app with PostgreSQL 14 (Universal)" from https://postgresapp.com/downloads.html (required for cx_Freeze build step)

```sh
cd desktop
python3 -m pip install poetry
/Library/Frameworks/Python.framework/Versions/3.10/bin/poetry install
/Library/Frameworks/Python.framework/Versions/3.10/bin/poetry run python ./scripts/get-tor.py macos
./scripts/build-pt-obfs4proxy.sh
./scripts/build-pt-snowflake.sh
./scripts/build-pt-meek.sh
/Library/Frameworks/Python.framework/Versions/3.10/bin/poetry run python ./setup-freeze.py build
/Library/Frameworks/Python.framework/Versions/3.10/bin/poetry run python ./setup-freeze.py bdist_mac
/Library/Frameworks/Python.framework/Versions/3.10/bin/poetry run python ./scripts/build-macos.py cleanup-build
cd build
tar -czvf ~/onionshare-macos-universal2.tar.gz OnionShare.app
```


Set up the packaging environment:

- Install create-dmg: `brew install create-dmg`

Github Actions will build the binaries. Find the Github Actions `build` workflow, switch to the summary tab, and download:

- `build-mac`

Extract these files, change to the `desktop` folder, and run:

```sh
poetry run python ./scripts/build-macos.py codesign [app_path]
poetry run python ./scripts/build-macos.py package [app_path]
```

The will create `dist/OnionShare-$VERSION.dmg`.

Now, notarize the release.

```sh
export APPLE_PASSWORD="changeme" # app-specific Apple ID password
export VERSION=$(cat ../cli/onionshare_cli/resources/version.txt)

# Notarize it
xcrun altool --notarize-app --primary-bundle-id "com.micahflee.onionshare" -u "micah@micahflee.com" -p "$APPLE_PASSWORD" --file dist/OnionShare-$VERSION.dmg
# Wait for it to get approved, check status with
xcrun altool --notarization-history 0 -u "micah@micahflee.com" -p "$APPLE_PASSWORD"
# After it's approved, staple the ticket
xcrun stapler staple dist/OnionShare-$VERSION.dmg
```

This will create `desktop/dist/OnionShare-$VERSION.dmg`, signed and notarized.

### Source package

To make a source package, run `./build-source.sh $TAG`, where `$TAG` is the name of the signed git tag, e.g. `v2.1`.

This will create `dist/onionshare-$VERSION.tar.gz`.

## Publishing the release

### PGP signatures

After following all of the previous steps, gather these files:

- `onionshare_${VERSION}_amd64.snap`
- `OnionShare.flatpak` (rename to `OnionShare-$VERSION.flatpak`)
- `OnionShare-win32-$VERSION.msi`
- `OnionShare-win64-$VERSION.msi`
- `OnionShare-$VERSION.dmg`
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
