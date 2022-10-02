# OnionShare Release Process

Unless you're a core OnionShare developer making a release, you'll probably never need to follow it.

## Changelog, version, docs, and signed git tag

Before making a release, you must update the version in these places:

- [ ] `cli/pyproject.toml`
- [ ] `cli/onionshare_cli/resources/version.txt`
- [ ] `desktop/pyproject.toml`
- [ ] `desktop/setup.py`
- [ ] `desktop/org.onionshare.OnionShare.appdata.xml`
- [ ] `docs/source/conf.py` (`version` at the top, and the `versions` list too)
- [ ] `snap/snapcraft.yaml`

If you update `flask-socketio`, ensure that you also update the [socket.io.min.js](https://github.com/micahflee/onionshare/blob/develop/cli/onionshare_cli/resources/static/js/socket.io.min.js) file to a version that is [supported](https://flask-socketio.readthedocs.io/en/latest/#version-compatibility) by the updated version of `flask-socketio`.

Update the documentation:

- [ ] Update all of the documentation in `docs` to cover new features, including taking new screenshots if necessary

Finalize localization:

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

You also must edit these files:

- [ ] `desktop/org.onionshare.OnionShare.appdata.xml` should have the correct release date, and links to correct screenshots
- [ ] `CHANGELOG.md` should be updated to include a list of all major changes since the last release

Make sure snapcraft packaging works. In `snap/snapcraft.yaml`:

- [ ] The `tor`, `libevent`, `obfs4`, `snowflake-client`, and `meek-client` parts should be updated if necessary
- [ ] All python packages in the `onionshare` part should be updated to match `desktop/pyproject.toml`
- [ ] With every commit to the `develop` branch, Snapcraft's CI should trigger builds. Make sure the builds all succeeded at https://snapcraft.io/onionshare/builds (you must be logged in), and test them

Update to the latest version of Tor:

- [ ] Edit `desktop/scripts/get-tor.py` to use the latest version of Tor Browser, and the latest sha256 checksums.
- [ ] Update the version of `meek`, `obfs4proxy`, and `snowflake` in the `desktop/scripts/build-pt-*` scripts, both the bash and PowerShell scripts.

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

Build and test the snap before publishing (note that `--dangerous` lets you install the snap before it's codesigned):

```sh
snapcraft
snap install --dangerous ./onionshare_${VERSION}_amd64.snap
```

This will create `onionshare_${VERSION}_amd64.snap`.

Run the OnionShare snap locally:

```sh
/snap/bin/onionshare     # desktop version
/snap/bin/onionshare.cli # CLI version
```

Upload the to Snapcraft:

```sh
snapcraft login
snapcraft upload --release=stable onionshare_${VERSION}_amd64.snap
```

## Windows

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

## macOS

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

## Source package

To make a source package, run `./build-source.sh $TAG`, where `$TAG` is the name of the signed git tag, e.g. `v2.1`.

This will create `dist/onionshare-$VERSION.tar.gz`.

## Publishing the release

### PGP signatures

After following all of the previous steps, gather these files:

- `onionshare_${VERSION}_amd64.snap`
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
