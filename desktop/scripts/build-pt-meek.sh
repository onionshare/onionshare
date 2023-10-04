#!/bin/bash
MEEK_TAG=v0.38.0

OS=$(uname -s)

mkdir -p ./build/meek
cd ./build/meek
git clone https://git.torproject.org/pluggable-transports/meek.git || echo "already cloned"
cd meek
git checkout $MEEK_TAG

if [ "$OS" == "Darwin" ]; then
    if [[ $(uname -m) == 'arm64' ]]; then
        go build -o ../../../onionshare/resources/tor/meek-client-arm64 ./meek-client
        GOOS=darwin GOARCH=amd64 go build -o ../../../onionshare/resources/tor/meek-client-amd64 ./meek-client
        lipo -create -output ../../../onionshare/resources/tor/meek-client ../../../onionshare/resources/tor/meek-client-arm64 ../../../onionshare/resources/tor/meek-client-amd64
        rm ../../../onionshare/resources/tor/meek-client-arm64 ../../../onionshare/resources/tor/meek-client-amd64
    elif [[ $(uname -m) == 'x86_64' ]]; then
        go build -o ../../../onionshare/resources/tor/meek-client ./meek-client
    fi
else
    go build -o ../../../onionshare/resources/tor/meek-client ./meek-client
fi
