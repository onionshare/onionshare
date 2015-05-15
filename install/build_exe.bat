REM use pyinstaller to builder a folder with onionshare.exe
pyinstaller -y install\onionshare-win.spec

REM sign onionshare.exe
signtool.exe sign /v /d "OnionShare" /a /tr "http://www.startssl.com/timestamp" dist\onionshare\onionshare.exe

REM run onionshare once, to compile the .py files into .pyc
dist\onionshare\onionshare.exe --help

REM build an installer, dist\OnionShare_Setup.exe
makensisw install\onionshare.nsi

REM sign OnionShare_Setup.exe
signtool.exe sign /v /d "OnionShare" /a /tr "http://www.startssl.com/timestamp" dist\OnionShare_Setup.exe
