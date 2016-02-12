#!/bin/bash

ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
cd $ROOT

# deleting dist
echo Deleting dist folder
rm -rf $ROOT/dist &>/dev/null 2>&1

# build the .app
echo Building OnionShare.app
python3 setup.py py2app

if [ "$1" = "--sign" ]; then
  SIGNING_IDENTITY_APP="Developer ID Application: Micah Lee"
  SIGNING_IDENTITY_INSTALLER="Developer ID Installer: Micah Lee"

  # codesign the .app
  python3 $ROOT/install/prepare_for_codesign.py
  cd dist

  # for some reason --deep fails, so sign each binary individually
  codesign -vvvv -s "Developer ID Application: Micah Lee" OnionShare.app/Contents/Frameworks/QtCore.framework
  codesign -vvvv -s "Developer ID Application: Micah Lee" OnionShare.app/Contents/Frameworks/QtGui.framework
  codesign -vvvv -s "Developer ID Application: Micah Lee" OnionShare.app/Contents/Frameworks/Python.framework
  codesign -vvvv -s "Developer ID Application: Micah Lee" OnionShare.app/Contents/Frameworks/libssl.1.0.0.dylib
  codesign -vvvv -s "Developer ID Application: Micah Lee" OnionShare.app/Contents/Frameworks/libcrypto.1.0.0.dylib
  codesign -vvvv -s "Developer ID Application: Micah Lee" OnionShare.app/Contents/MacOS/python
  codesign -vvvv -s "Developer ID Application: Micah Lee" OnionShare.app

  productbuild --component OnionShare.app /Applications OnionShare.pkg --sign "$SIGNING_IDENTITY_INSTALLER"
fi
