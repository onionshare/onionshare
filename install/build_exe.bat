REM delete old build files
rmdir /s /q build
rmdir /s /q dist

REM build onionshare-gui.exe
pyinstaller install\pyinstaller.spec -y

REM sign onionshare-gui.exe
signtool.exe sign /v /d "OnionShare" /a /tr http://timestamp.globalsign.com/scripts/timstamp.dll /fd sha256 dist\onionshare\onionshare-gui.exe

REM build an installer, dist\OnionShare_Setup.exe
makensis.exe install\onionshare.nsi

REM sign OnionShare_Setup.exe
signtool.exe sign /v /d "OnionShare" /a /tr http://timestamp.globalsign.com/scripts/timstamp.dll /fd sha256 dist\OnionShare_Setup.exe
