#!/bin/bash

export DEVELOPER_ID="Developer ID Application: Micah Lee (N9B95FDWH4)"

# Cleanb up from the last build
rm -rf macOS
briefcase create

# Codesign the child binaries
codesign --sign "$DEVELOPER_ID" \
    --entitlements install/macos_sandbox/ChildEntitlements.plist \
    macOS/OnionShare/OnionShare.app/Contents/Resources/app/onionshare/resources/tor/tor \
    --force --options runtime
codesign --sign "$DEVELOPER_ID" \
    --entitlements install/macos_sandbox/ChildEntitlements.plist \
    macOS/OnionShare/OnionShare.app/Contents/Resources/app/onionshare/resources/tor/libevent-2.1.7.dylib \
    --force --options runtime
codesign --sign "$DEVELOPER_ID" \
    --entitlements install/macos_sandbox/ChildEntitlements.plist \
    macOS/OnionShare/OnionShare.app/Contents/Resources/app/onionshare/resources/tor/obfs4proxy \
    --force --options runtime

# Build and codesign the app bundle and dmg
cp install/macos_sandbox/Entitlements.plist macOS/OnionShare/
briefcase package -i "$DEVELOPER_ID"
