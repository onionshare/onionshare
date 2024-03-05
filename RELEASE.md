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

Update the versions of `meek`, `obfs4proxy`, and `snowflake` in the `desktop/scripts/build-pt-*` scripts, both the bash and PowerShell scripts. You can find the latest versions by looking at the tags in their git repos: [meek](https://gitlab.torproject.org/tpo/anti-censorship/pluggable-transports/meek/-/tags), [obfs4proxy](https://gitlab.com/yawning/obfs4/-/tags), [snowflake](https://gitlab.torproject.org/tpo/anti-censorship/pluggable-transports/snowflake/-/tags).

### Update the documentation

- [ ] Update all of the documentation in `docs` to cover new features, including taking new screenshots if necessary

### Finalize localization

- [ ] Merge all the translations from weblate:
      ```
      git remote add weblate https://hosted.weblate.org/projects/onionshare/translations/
      git pull weblate main
      ```
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

To test locally:

- Install snapcraft with: `sudo snap install snapcraft --classic`
- Build snap with: `snapcraft`
- Install with: `sudo snap install ./onionshare_${VERSION}_amd64.snap --devmode`

To test in the edge branch:

With every commit to the `main` branch, Snapcraft's CI should trigger builds. Make sure the builds all succeeded at https://snapcraft.io/onionshare/builds (you must be logged in), and test them. You can install them with: `snap install onionshare --edge`

### Make sure the Flatpak packaging works

In `flatpak/org.onionshare.OnionShare.yaml`:

- [ ] Update `tor` and `libevent`
- [ ] Update `obfs4proxy`, `meek-client`, and `snowflake-client` dependencies, if necessary using [this tool](https://github.com/micahflee/flatpak-builder-tools/tree/fix-go/go):
  ```sh
  cd flatpak-builder-tools/go

  # For each these, incorporate the output into the Flatpak manifest
  # Make sure to update the version numbers
  ./flatpak-go-deps.py git.torproject.org/pluggable-transports/meek.git/meek-client@v0.38.0
  ./flatpak-go-deps.py git.torproject.org/pluggable-transports/snowflake.git/client@v2.6.0
  ./flatpak-go-deps.py gitlab.com/yawning/obfs4.git/obfs4proxy@obfs4proxy-0.0.14
  ```
  Merge the output of each of these commands into the Flatpak manifest.
- [ ] Update the Python dependencies using [this tool](https://github.com/flatpak/flatpak-builder-tools/blob/master/pip/flatpak-pip-generator) along with `flatpak/poetry-to-requirements.py`:
  ```sh
  cd flatpak-build-tools/pip

  # get onionshare-cli dependencies
  ./flatpak-pip-generator $(../../onionshare/flatpak/poetry-to-requirements.py ../../onionshare/cli/pyproject.toml)
  ../flatpak-json2yaml.py ./python3-modules.json
  mv python3-modules.yml onionshare-cli.yaml

  # get onionshare dependencies
  ./flatpak-pip-generator $(../../onionshare/flatpak/poetry-to-requirements.py ../../onionshare/desktop/pyproject.toml | grep -v PySide6)
  ../flatpak-json2yaml.py ./python3-modules.json
  mv python3-modules.yml onionshare-desktop.yaml
  ```
  Now, merge `onionshare-desktop.yaml` and `onionshare-cli.yaml` into the Flatpak manifest.
- [ ] Build and test the Flatpak package to ensure it works:
  ```sh
  flatpak-builder build --force-clean --jobs=$(nproc) --install-deps-from=flathub --install --user flatpak/org.onionshare.OnionShare.yaml
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

Create a Windows 11 VM, and set it up like this:

- Install [git for Windows](https://git-scm.com/download/win).
- Install the latest version of 3.11 [from python.org](https://www.python.org/downloads/).
- Install [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/), making sure to check "Desktop development with C++".
- Download and install [7-Zip (x64)](https://7-zip.org/). Add `C:\Program Files\7-Zip` to your path.
- Download and install [gpg4win](https://gpg4win.org/). Add `C:\Program Files (x86)\GnuPG\bin` to your path.
- Install the Windows SDK from here: https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/.
- Go to https://dotnet.microsoft.com/download/dotnet-framework and download and install .NET Framework 3.5 SP1 Runtime. I downloaded `dotnetfx35.exe`.
- Go to https://wixtoolset.org/docs/wix3/ and download and install WiX toolset. I downloaded `wix311.exe`. Add `C:\Program Files (x86)\WiX Toolset v3.11\bin` to the path.

Clone the OnionShare git repo and checkout the release tag.

If you've used this git repo for a previous release, clean it up:

- In the `onionshare/desktop` folder, delete `build` and `dist` from the previous build.
- Delete the poetry environment. You can find its name by run `poetry env list`, and then you can delete it with `poetry env remove [ENV_NAME]`.

Install Poetry and deps. Open a Developer PowerShell for VS window, change to the `onionshare` folder, and run:

```powershell
cd desktop
pip install poetry
poetry install
```

Github Actions will build the binaries. Find the Github Actions `build` workflow, switch to the summary tab, download `win64-build.zip`, and copy it to the Windows packaging environment.

Extract `win64-build.zip`. Run:

```
poetry run python .\scripts\build-windows.py codesign [path]
poetry run python .\scripts\build-windows.py package [path]
```

This will create:

- `desktop/dist/OnionShare-win64-$VERSION.msi`

### macOS release

In order to make a universal2 binary, you must following these instructions using a Mac with Apple Silicon. To keep a clean environment, you can use VM.

Set up the VM like this:

- Install [Homebrew](https://brew.sh/)
- `brew install create-dmg libiodbc`
- Install the latest Python 3.12 from https://www.python.org/downloads/
- Install ARM64 version of Go from https://go.dev/dl/
- Install "Postgres.app with PostgreSQL 16 (Universal)" from https://postgresapp.com/downloads.html

Clone the OnionShare git repo and checkout the release tag.

If you've used this git repo for a previous release, clean it up:

```sh
cd desktop
rm -rf build dist
# Delete the old poetry environment
poetry env remove $(poetry env list | grep "(Activated)" | cut -d" " -f1)
```

Install and build dependencies:

```sh
cd desktop
python3 -m pip install poetry
/Library/Frameworks/Python.framework/Versions/3.12/bin/poetry install
/Library/Frameworks/Python.framework/Versions/3.12/bin/poetry run python ./scripts/get-tor.py macos
./scripts/build-pt-obfs4proxy.sh
./scripts/build-pt-snowflake.sh
./scripts/build-pt-meek.sh
```

Make the Apple Silicon app bundle:

```sh
/Library/Frameworks/Python.framework/Versions/3.11/bin/poetry run python ./setup-freeze.py bdist_mac
/Library/Frameworks/Python.framework/Versions/3.11/bin/poetry run python ./scripts/build-macos.py cleanup-build
```

The Apple Silicon app bundle will be in `build` folder called `OnionShare.app`.

Github Actions will build the Intel app bundle. Find the Github Actions `build` workflow, switch to the summary tab, and download the `mac-intel-build` artifact. Extract it, and you'll get the Intel `OnionShare.app` folder.

Next, merge these two app bundles into a single universal2 app bundle:

```sh
poetry run ./scripts/macos-merge-universal.py [intel_app_path] [silicon_app_path] [universal2_app_path]
```

Finally, code sign and package the universal2 app bundle:

```sh
poetry run python ./scripts/build-macos.py codesign [universal2_app_path]
poetry run python ./scripts/build-macos.py package [universal2_app_path]
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
