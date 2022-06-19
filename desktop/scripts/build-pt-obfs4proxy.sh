#!/bin/bash
OBFS4PROXY_TAG=obfs4proxy-0.0.13

mkdir -p ./build/obfs4proxy
cd ./build/obfs4proxy
git clone https://gitlab.com/yawning/obfs4 || echo "already cloned"
cd obfs4
git checkout $OBFS4PROXY_TAG
go build -o ../../../onionshare/resources/tor/obfs4proxy ./obfs4proxy