#!/bin/bash

ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
cd $ROOT

# deleting dist
echo Deleting dist folder
rm -rf $ROOT/dist &>/dev/null 2>&1

# build the .app
echo Building OnionShare.app
pyinstaller install/pyinstaller-osx.spec

if [ "$1" = "--sign" ]; then
  SIGNING_IDENTITY_APP="3rd Party Mac Developer Application: Micah Lee"
  SIGNING_IDENTITY_INSTALLER="3rd Party Mac Developer Installer: Micah Lee"

  # codesign the .app
  codesign -vvvv --deep -s "$SIGNING_IDENTITY_APP" dist/OnionShare.app

  # build .pkg
  productbuild --component dist/OnionShare.app /Applications dist/OnionShare.pkg --sign "$SIGNING_IDENTITY_INSTALLER"
fi
