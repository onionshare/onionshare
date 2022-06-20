$env:SNOWFLAKE_TAG = 'v2.2.0'

New-Item -ItemType Directory -Force -Path .\build\snowflake
cd .\build\snowflake
git clone https://git.torproject.org/pluggable-transports/snowflake.git
cd snowflake
git checkout $SNOWFLAKE_TAG
go build .\client
Move-Item -Path .\client.exe -Destination ..\..\..\onionshare\resources\tor\snowflake-client.exe
