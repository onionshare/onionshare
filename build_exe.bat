REM use pyinstaller to builder a folder with onionshare.exe
pyinstaller -y setup\onionshare-win.spec

REM run onionshare once, to compile the .py files into .pyc
dist\onionshare\onionshare.exe --help

REM build an installer, dist\OnionShare_Setup.exe
makensisw setup\onionshare.nsi