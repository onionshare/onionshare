$env:WEBTUNNEL_TAG = 'v0.0.7'

New-Item -ItemType Directory -Force -Path .\build\webtunnel
cd .\build\webtunnel
git clone https://gitlab.torproject.org/tpo/anti-censorship/pluggable-transports/webtunnel.git
cd webtunnel
git checkout $env:WEBTUNNEL_TAG
go build -o webtunnel-client.exe .\main\client
Move-Item -Path .\webtunnel-client.exe -Destination ..\..\..\onionshare\resources\tor\webtunnel-client.exe
