REM build onionshare.exe, onionshare-gui.exe
python setup.py build

REM sign onionshare.exe, onionshare-gui.exe
signtool.exe sign /v /d "OnionShare" /a /tr http://timestamp.globalsign.com/scripts/timstamp.dll /fd sha256 build\exe.win32-3.5\onionshare.exe
signtool.exe sign /v /d "OnionShare" /a /tr http://timestamp.globalsign.com/scripts/timstamp.dll /fd sha256 build\exe.win32-3.5\onionshare-gui.exe

REM build an installer, dist\OnionShare_Setup.exe
mkdir dist
makensis.exe install\onionshare.nsi

REM sign OnionShare_Setup.exe
signtool.exe sign /v /d "OnionShare" /a /tr http://timestamp.globalsign.com/scripts/timstamp.dll /fd sha256 dist\OnionShare_Setup.exe
