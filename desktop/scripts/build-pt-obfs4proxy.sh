#!/bin/bash
OBFS4PROXY_TAG=obfs4proxy-0.0.14

OS=$(uname -s)

mkdir -p ./build/obfs4proxy
cd ./build/obfs4proxy
git clone https://gitlab.com/yawning/obfs4 || echo "already cloned"
cd obfs4
git checkout $OBFS4PROXY_TAG
if [ "$OS" == "Darwin" ]; then
    if [[ $(uname -m) == 'arm64' ]]; then
        go build -o ../../../onionshare/resources/tor/obfs4proxy-arm64 ./obfs4proxy
        GOOS=darwin GOARCH=amd64 go build -o ../../../onionshare/resources/tor/obfs4proxy-amd64 ./obfs4proxy
        lipo -create -output ../../../onionshare/resources/tor/obfs4proxy ../../../onionshare/resources/tor/obfs4proxy-arm64 ../../../onionshare/resources/tor/obfs4proxy-amd64
        rm ../../../onionshare/resources/tor/obfs4proxy-arm64 ../../../onionshare/resources/tor/obfs4proxy-amd64
    elif [[ $(uname -m) == 'x86_64' ]]; then
        go build -o ../../../onionshare/resources/tor/obfs4proxy ./obfs4proxy
    fi
else
    go build -o ../../../onionshare/resources/tor/obfs4proxy ./obfs4proxy
fi
