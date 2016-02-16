REM use py2exe to builder a folder with onionshare.exe
python setup.py py2exe

REM sign onionshare.exe
signtool.exe sign /v /d "OnionShare" /a /tr http://timestamp.globalsign.com/scripts/timstamp.dll /fd sha256 dist\onionshare.exe

REM build an installer, dist\OnionShare_Setup.exe
makensis.exe install\onionshare.nsi

REM sign OnionShare_Setup.exe
signtool.exe sign /v /d "OnionShare" /a /tr http://timestamp.globalsign.com/scripts/timstamp.dll /fd sha256 dist\OnionShare_Setup.exe
