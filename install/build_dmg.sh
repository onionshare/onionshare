#!/bin/bash

ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
DMG_DIR=$ROOT/dist/dmg
DMG_TMP_NAME=$ROOT/dist/tmp.dmg
DMG_NAME=$ROOT/dist/OnionShare.dmg
TITLE=OnionShare
VOLUME=/Volumes/$TITLE

cd $ROOT

# deleting dist
echo Deleting dist folder
rm -rf $ROOT/dist &>/dev/null 2>&1

# build the .app
echo Building OnionShare.app
pyinstaller -w -y $ROOT/setup/onionshare-osx.spec

# create the .dmg
echo Creating DMG
mkdir -p $DMG_DIR
hdiutil create -srcfolder $DMG_DIR -volname $TITLE -fs HFS+ -fsargs "-c c=64,a=16,e=16" -format UDRW -size 100mb $DMG_TMP_NAME
DEVICE=$(hdiutil attach -readwrite -noverify -noautoopen $DMG_TMP_NAME | egrep '^/dev/' | sed 1q | awk '{print $1}')
sleep 10

# set up the dmg
echo Setting up DMG
cp -r $ROOT/dist/OnionShare.app $VOLUME
ln -s /Applications $VOLUME/Applications
mkdir $VOLUME/.background
cp $ROOT/setup/dmg_background.png $VOLUME/.background/background.png
echo '
   tell application "Finder"
     tell disk "'${TITLE}'"
           open
           set current view of container window to icon view
           set toolbar visible of container window to false
           set statusbar visible of container window to false
           set the bounds of container window to {100, 100, 400, 480}
           set theViewOptions to the icon view options of container window
           set arrangement of theViewOptions to not arranged
           set icon size of theViewOptions to 72
           set background picture of theViewOptions to file ".background:background.png"
           set position of item "'${TITLE}.app'" of container window to {60, 288}
           set position of item "Applications" of container window to {268, 288}
           update without registering applications
           delay 10
           eject
     end tell
   end tell
' | osascript

# finalize the DMG
echo Finalizing DMG
hdiutil convert $DMG_TMP_NAME -format UDZO -imagekey zlib-level=9 -o $DMG_NAME
rm -r $DMG_DIR
rm -f $DMG_TMP_NAME

# all done
echo DMG created: $DMG_NAME
