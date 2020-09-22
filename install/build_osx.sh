#!/bin/bash

ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
cd $ROOT

# deleting dist
echo Deleting dist folder
rm -rf $ROOT/dist &>/dev/null 2>&1

# build the .app
echo Building OnionShare.app
pyinstaller $ROOT/install/pyinstaller.spec
python3 $ROOT/install/get-tor-osx.py

# create a symlink of onionshare-gui called onionshare, for the CLI version
cd $ROOT/dist/OnionShare.app/Contents/MacOS
ln -s onionshare-gui onionshare
cd $ROOT

if [ "$1" = "--release" ]; then
  mkdir -p dist
  APP_PATH="$ROOT/dist/OnionShare.app"
  IDENTITY_NAME_APPLICATION="Developer ID Application: Micah Lee (N9B95FDWH4)"
  ENTITLEMENTS_CHILD_PATH="$ROOT/install/macos_sandbox/child.plist"
  ENTITLEMENTS_PARENT_PATH="$ROOT/install/macos_sandbox/parent.plist"

  echo "Codesigning the app bundle"
  codesign \
    --deep \
    -s "$IDENTITY_NAME_APPLICATION" \
    -o runtime \
    --force \
    --entitlements "$ENTITLEMENTS_CHILD_PATH" \
    --timestamp \
    "$APP_PATH"
  codesign \
    -s "$IDENTITY_NAME_APPLICATION" \
    -o runtime \
    --force \
    --entitlements "$ENTITLEMENTS_PARENT_PATH" \
    --timestamp \
    "$APP_PATH"

  echo "Create the DMG"
  if [ ! -f "/usr/local/bin/create-dmg" ]; then
    echo "Error: create-dmg is not installed"
    exit 0
  fi
  /usr/local/bin/create-dmg "$APP_PATH" --identity "$IDENTITY_NAME_APPLICATION"
  mv *.dmg dist

  echo "Cleaning up"
  rm -rf "$APP_PATH"

  echo "All done, your DMG is in:"
  ls dist/*.dmg
fi
