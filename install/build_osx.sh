#!/bin/bash

ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
cd $ROOT

# deleting dist
echo Deleting dist folder
rm -rf $ROOT/build $ROOT/dist &>/dev/null 2>&1

# build the .app
echo Building OnionShare.app
pyinstaller install/pyinstaller.spec

if [ "$1" = "--release" ]; then
  mkdir -p dist
  APP_PATH="build/OnionShare.app"
  PKG_PATH="dist/OnionShare.pkg"
  IDENTITY_NAME_APPLICATION="Developer ID Application: Micah Lee"
  IDENTITY_NAME_INSTALLER="Developer ID Installer: Micah Lee"

  echo "Codesigning the app bundle"
  codesign --deep -s "$IDENTITY_NAME_APPLICATION" "$APP_PATH"

  echo "Creating an installer"
  productbuild --sign "$IDENTITY_NAME_INSTALLER" --component "$APP_PATH" /Applications "$PKG_PATH"

  echo "Cleaning up"
  rm -rf "$APP_PATH"

  echo "All done, your installer is in: $PKG_PATH"
fi
