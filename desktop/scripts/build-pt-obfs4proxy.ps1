$env:OBFS4PROXY_TAG = 'obfs4proxy-0.0.13'

New-Item -ItemType Directory -Force -Path .\build\obfs4proxy
cd .\build\obfs4proxy
git clone https://gitlab.com/yawning/obfs4
cd obfs4
git checkout $OBFS4PROXY_TAG
go build .\obfs4proxy
Move-Item -Path .\obfs4proxy.exe -Destination ..\..\..\onionshare\resources\tor\obfs4proxy.exe
