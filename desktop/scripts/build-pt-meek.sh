#!/bin/bash
MEEK_TAG=v0.37.0

mkdir -p ./build/meek
cd ./build/meek
git clone https://git.torproject.org/pluggable-transports/meek.git
cd meek
git checkout $MEEK_TAG
go build -o ../../../onionshare/resources/tor/meek-client ./meek-client
