$env:MEEK_TAG = 'v0.37.0'

New-Item -ItemType Directory -Force -Path .\build\meek
cd .\build\meek
git clone https://git.torproject.org/pluggable-transports/meek.git
cd meek
git checkout $MEEK_TAG
go build .\meek-client
Move-Item -Path .\meek-client.exe -Destination ..\..\..\onionshare\resources\tor\meek-client.exe
