#!/bin/bash
SNOWFLAKE_TAG=v2.8.1

OS=$(uname -s)

mkdir -p ./build/snowflake
cd ./build/snowflake
git clone https://gitlab.torproject.org/tpo/anti-censorship/pluggable-transports/snowflake.git || echo "already cloned"
cd snowflake
git checkout $SNOWFLAKE_TAG
if [ "$OS" == "Darwin" ]; then
    if [[ $(uname -m) == 'arm64' ]]; then
        go build -o ../../../onionshare/resources/tor/snowflake-client-arm64 ./client
        GOOS=darwin GOARCH=amd64 go build -o ../../../onionshare/resources/tor/snowflake-client-amd64 ./client
        lipo -create -output ../../../onionshare/resources/tor/snowflake-client ../../../onionshare/resources/tor/snowflake-client-arm64 ../../../onionshare/resources/tor/snowflake-client-amd64
        rm ../../../onionshare/resources/tor/snowflake-client-arm64 ../../../onionshare/resources/tor/snowflake-client-amd64
    elif [[ $(uname -m) == 'x86_64' ]]; then
        go build -o ../../../onionshare/resources/tor/snowflake-client ./client
    fi
else
    go build -o ../../../onionshare/resources/tor/snowflake-client ./client
fi
