REM delete old dist files
rmdir /s /q dist

REM build onionshare-gui.exe
pyinstaller install\pyinstaller.spec -y

REM download tor
python install\get-tor-windows.py

REM sign onionshare-gui.exe
REM signtool.exe sign /v /d "OnionShare" /a /tr http://timestamp.globalsign.com/scripts/timstamp.dll /fd sha256 dist\onionshare\onionshare-gui.exe

REM build an installer, dist\OnionShare_Setup.exe
makensis.exe install\onionshare.nsi

REM sign OnionShare_Setup.exe
REM signtool.exe sign /v /d "OnionShare" /a /tr http://timestamp.globalsign.com/scripts/timstamp.dll /fd sha256 dist\OnionShare_Setup.exe
