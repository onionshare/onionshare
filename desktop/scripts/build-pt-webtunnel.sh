#!/bin/bash
WEBTUNNEL_TAG=v0.0.1

OS=$(uname -s)

mkdir -p ./build/webtunnel
cd ./build/webtunnel
git clone https://gitlab.torproject.org/tpo/anti-censorship/pluggable-transports/webtunnel.git || echo "already cloned"
cd webtunnel
git checkout $WEBTUNNEL_TAG
if [ "$OS" == "Darwin" ]; then
    if [[ $(uname -m) == 'arm64' ]]; then
        go build -o ../../../onionshare/resources/tor/webtunnel-client-arm64 ./client
        GOOS=darwin GOARCH=amd64 go build -o ../../../onionshare/resources/tor/webtunnel-client-amd64 ./client
        lipo -create -output ../../../onionshare/resources/tor/webtunnel-client ../../../onionshare/resources/tor/webtunnel-client-arm64 ../../../onionshare/resources/tor/webtunnel-client-amd64
        rm ../../../onionshare/resources/tor/webtunnel-client-arm64 ../../../onionshare/resources/tor/webtunnel-client-amd64
    elif [[ $(uname -m) == 'x86_64' ]]; then
        go build -o ../../../onionshare/resources/tor/webtunnel-client ./client
    fi
else
    go build -o ../../../onionshare/resources/tor/webtunnel-client ./client
fi
