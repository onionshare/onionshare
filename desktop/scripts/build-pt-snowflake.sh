#!/bin/bash
SNOWFLAKE_TAG=v2.2.0

mkdir -p ./build/snowflake
cd ./build/snowflake
git clone https://git.torproject.org/pluggable-transports/snowflake.git
cd snowflake
git checkout $SNOWFLAKE_TAG
go build -o ../../../onionshare/resources/tor/snowflake-client ./client
