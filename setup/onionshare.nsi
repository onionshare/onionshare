!define APPNAME "OnionShare"
!define BINPATH "..\dist\onionshare"
!define ABOUTURL "https://onionshare.org/"

# change these with each release
!define INSTALLSIZE 31187
!define VERSIONMAJOR 0
!define VERSIONMINOR 6
!define VERSIONSTRING "0.6"

RequestExecutionLevel admin

SetCompressor /FINAL /SOLID lzma

Name "OnionShare"
InstallDir "$PROGRAMFILES\${APPNAME}"
LicenseData "license.txt"
Icon "onionshare.ico"
OutFile "..\dist\OnionShare_Setup.exe"

!include LogicLib.nsh

Page license
Page directory
Page instfiles

!macro VerifyUserIsAdmin
UserInfo::GetAccountType
pop $0
${If} $0 != "admin" ;Require admin rights on NT4+
    messageBox mb_iconstop "Administrator rights required!"
    setErrorLevel 740 ;ERROR_ELEVATION_REQUIRED
    quit
${EndIf}
!macroend

Function .onInit
    setShellVarContext all
    !insertmacro VerifyUserIsAdmin
FunctionEnd

Section "install"
    # application
    SetOutPath "$INSTDIR"
    File "onionshare.ico"
    File "${BINPATH}\onionshare.exe"
    File "${BINPATH}\LICENSE"
    SetOutPath "$INSTDIR\onionshare"
    File "${BINPATH}\onionshare\__init__.py"
    File "${BINPATH}\onionshare\__init__.pyc"
    File "${BINPATH}\onionshare\404.html"
    File "${BINPATH}\onionshare\helpers.py"
    File "${BINPATH}\onionshare\helpers.pyc"
    File "${BINPATH}\onionshare\index.html"
    File "${BINPATH}\onionshare\onionshare.py"
    File "${BINPATH}\onionshare\onionshare.pyc"
    File "${BINPATH}\onionshare\socks.py"
    File "${BINPATH}\onionshare\socks.pyc"
    File "${BINPATH}\onionshare\strings.py"
    File "${BINPATH}\onionshare\strings.pyc"
    File "${BINPATH}\onionshare\web.py"
    File "${BINPATH}\onionshare\web.pyc"
    SetOutPath "$INSTDIR\onionshare_gui"
    File "${BINPATH}\onionshare_gui\__init__.py"
    File "${BINPATH}\onionshare_gui\__init__.pyc"
    File "${BINPATH}\onionshare_gui\common.py"
    File "${BINPATH}\onionshare_gui\common.pyc"
    File "${BINPATH}\onionshare_gui\downloads.py"
    File "${BINPATH}\onionshare_gui\downloads.pyc"
    File "${BINPATH}\onionshare_gui\file_selection.py"
    File "${BINPATH}\onionshare_gui\file_selection.pyc"
    File "${BINPATH}\onionshare_gui\onionshare_gui.py"
    File "${BINPATH}\onionshare_gui\onionshare_gui.pyc"
    File "${BINPATH}\onionshare_gui\options.py"
    File "${BINPATH}\onionshare_gui\options.pyc"
    File "${BINPATH}\onionshare_gui\server_status.py"
    File "${BINPATH}\onionshare_gui\server_status.pyc"
    SetOutPath "$INSTDIR\images"
    File "${BINPATH}\images\logo.png"
    File "${BINPATH}\images\drop_files.png"
    File "${BINPATH}\images\server_stopped.png"
    File "${BINPATH}\images\server_started.png"
    File "${BINPATH}\images\server_working.png"
    SetOutPath "$INSTDIR\locale"
    File "${BINPATH}\locale\de.json"
    File "${BINPATH}\locale\en.json"
    File "${BINPATH}\locale\es.json"
    File "${BINPATH}\locale\fi.json"
    File "${BINPATH}\locale\fr.json"
    File "${BINPATH}\locale\it.json"
    File "${BINPATH}\locale\nl.json"
    File "${BINPATH}\locale\no.json"
    File "${BINPATH}\locale\pt.json"
    File "${BINPATH}\locale\ru.json"
    File "${BINPATH}\locale\tr.json"

    # dependencies
    SetOutPath $INSTDIR
    File "${BINPATH}\_ctypes.pyd"
    File "${BINPATH}\_hashlib.pyd"
    File "${BINPATH}\_socket.pyd"
    File "${BINPATH}\_ssl.pyd"
    File "${BINPATH}\bz2.pyd"
    File "${BINPATH}\Microsoft.VC90.CRT.manifest"
    File "${BINPATH}\msvcm90.dll"
    File "${BINPATH}\msvcp90.dll"
    File "${BINPATH}\msvcr90.dll"
    File "${BINPATH}\onionshare.exe.manifest"
    File "${BINPATH}\pyexpat.pyd"
    File "${BINPATH}\PyQt4.QtCore.pyd"
    File "${BINPATH}\PyQt4.QtGui.pyd"
    File "${BINPATH}\python27.dll"
    File "${BINPATH}\pywintypes27.dll"
    File "${BINPATH}\QtCore4.dll"
    File "${BINPATH}\QtGui4.dll"
    File "${BINPATH}\QtOpenGL4.dll"
    File "${BINPATH}\QtSvg4.dll"
    File "${BINPATH}\QtXml4.dll"
    File "${BINPATH}\select.pyd"
    File "${BINPATH}\sip.pyd"
    File "${BINPATH}\unicodedata.pyd"
    File "${BINPATH}\win32api.pyd"
    File "${BINPATH}\win32pipe.pyd"
    File "${BINPATH}\win32wnet.pyd"
    SetOutPath "$INSTDIR\qt4_plugins\accessible"
    File "${BINPATH}\qt4_plugins\accessible\qtaccessiblewidgets4.dll"
    SetOutPath "$INSTDIR\qt4_plugins\codecs"
    File "${BINPATH}\qt4_plugins\codecs\qcncodecs4.dll"
    File "${BINPATH}\qt4_plugins\codecs\qjpcodecs4.dll"
    File "${BINPATH}\qt4_plugins\codecs\qkrcodecs4.dll"
    File "${BINPATH}\qt4_plugins\codecs\qtwcodecs4.dll"
    SetOutPath "$INSTDIR\qt4_plugins\graphicssystems"
    File "${BINPATH}\qt4_plugins\graphicssystems\qglgraphicssystem4.dll"
    SetOutPath "$INSTDIR\qt4_plugins\iconengines"
    File "${BINPATH}\qt4_plugins\iconengines\qsvgicon4.dll"
    SetOutPath "$INSTDIR\qt4_plugins\imageformats"
    File "${BINPATH}\qt4_plugins\imageformats\qgif4.dll"
    File "${BINPATH}\qt4_plugins\imageformats\qico4.dll"
    File "${BINPATH}\qt4_plugins\imageformats\qjpeg4.dll"
    File "${BINPATH}\qt4_plugins\imageformats\qmng4.dll"
    File "${BINPATH}\qt4_plugins\imageformats\qsvg4.dll"
    File "${BINPATH}\qt4_plugins\imageformats\qtga4.dll"
    File "${BINPATH}\qt4_plugins\imageformats\qtiff4.dll"
    SetOutPath "$INSTDIR\Include"
    File "${BINPATH}\Include\pyconfig.h"

    # uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"

    # start menu
    CreateShortCut "$SMPROGRAMS\${APPNAME}.lnk" "$INSTDIR\onionshare.exe" "" "$INSTDIR\onionshare.ico"

    # registry information for add/remove programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "QuietUninstallString" "$\"$INSTDIR\uninstall.exe$\" /S"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "InstallLocation" "$\"$INSTDIR$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayIcon" "$\"$INSTDIR\onionshare.ico$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLInfoAbout" "$\"${ABOUTURL}$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayVersion" ${VERSIONSTRING}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "VersionMajor" ${VERSIONMAJOR}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "VersionMinor" ${VERSIONMINOR}
    # there is no option for modifying or repairing the install
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoRepair" 1
    # set the INSTALLSIZE constant (!defined at the top of this script) so Add/Remove Programs can accurately report the size
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "EstimatedSize" ${INSTALLSIZE}
SectionEnd

# uninstaller
Function un.onInit
    SetShellVarContext all

    #Verify the uninstaller - last chance to back out
    MessageBox MB_OKCANCEL "Uninstall ${APPNAME}?" IDOK next
        Abort
    next:
    !insertmacro VerifyUserIsAdmin
FunctionEnd

Section "uninstall"
    Delete "$SMPROGRAMS\${APPNAME}.lnk"

    # remove files
    Delete "$INSTDIR\onionshare.exe"
    Delete "$INSTDIR\LICENSE"
    Delete "$INSTDIR\onionshare.ico"
    Delete "$INSTDIR\uninstall.exe"
    Delete "$INSTDIR\onionshare\__init__.py"
    Delete "$INSTDIR\onionshare\__init__.pyc"
    Delete "$INSTDIR\onionshare\404.html"
    Delete "$INSTDIR\onionshare\helpers.py"
    Delete "$INSTDIR\onionshare\helpers.pyc"
    Delete "$INSTDIR\onionshare\index.html"
    Delete "$INSTDIR\onionshare\onionshare.py"
    Delete "$INSTDIR\onionshare\onionshare.pyc"
    Delete "$INSTDIR\onionshare\socks.py"
    Delete "$INSTDIR\onionshare\socks.pyc"
    Delete "$INSTDIR\onionshare\strings.py"
    Delete "$INSTDIR\onionshare\strings.pyc"
    Delete "$INSTDIR\onionshare\web.py"
    Delete "$INSTDIR\onionshare\web.pyc"
    Delete "$INSTDIR\onionshare_gui\__init__.py"
    Delete "$INSTDIR\onionshare_gui\__init__.pyc"
    Delete "$INSTDIR\onionshare_gui\common.py"
    Delete "$INSTDIR\onionshare_gui\common.pyc"
    Delete "$INSTDIR\onionshare_gui\downloads.py"
    Delete "$INSTDIR\onionshare_gui\downloads.pyc"
    Delete "$INSTDIR\onionshare_gui\file_selection.py"
    Delete "$INSTDIR\onionshare_gui\file_selection.pyc"
    Delete "$INSTDIR\onionshare_gui\onionshare_gui.py"
    Delete "$INSTDIR\onionshare_gui\onionshare_gui.pyc"
    Delete "$INSTDIR\onionshare_gui\options.py"
    Delete "$INSTDIR\onionshare_gui\options.pyc"
    Delete "$INSTDIR\onionshare_gui\server_status.py"
    Delete "$INSTDIR\onionshare_gui\server_status.pyc"
    Delete "$INSTDIR\images\logo.png"
    Delete "$INSTDIR\images\drop_files.png"
    Delete "$INSTDIR\images\server_stopped.png"
    Delete "$INSTDIR\images\server_started.png"
    Delete "$INSTDIR\images\server_working.png"
    Delete "$INSTDIR\locale\de.json"
    Delete "$INSTDIR\locale\en.json"
    Delete "$INSTDIR\locale\es.json"
    Delete "$INSTDIR\locale\fi.json"
    Delete "$INSTDIR\locale\fr.json"
    Delete "$INSTDIR\locale\it.json"
    Delete "$INSTDIR\locale\nl.json"
    Delete "$INSTDIR\locale\no.json"
    Delete "$INSTDIR\locale\pt.json"
    Delete "$INSTDIR\locale\ru.json"
    Delete "$INSTDIR\locale\tr.json"
    Delete "$INSTDIR\qt4_plugins\accessible\qtaccessiblewidgets4.dll"
    Delete "$INSTDIR\qt4_plugins\graphicssystems\qglgraphicssystem4.dll"
    Delete "$INSTDIR\qt4_plugins\iconengines\qsvgicon4.dll"
    Delete "$INSTDIR\qt4_plugins\codecs\qjpcodecs4.dll"
    Delete "$INSTDIR\qt4_plugins\codecs\qkrcodecs4.dll"
    Delete "$INSTDIR\qt4_plugins\codecs\qtwcodecs4.dll"
    Delete "$INSTDIR\qt4_plugins\codecs\qcncodecs4.dll"
    Delete "$INSTDIR\qt4_plugins\imageformats\qmng4.dll"
    Delete "$INSTDIR\qt4_plugins\imageformats\qico4.dll"
    Delete "$INSTDIR\qt4_plugins\imageformats\qgif4.dll"
    Delete "$INSTDIR\qt4_plugins\imageformats\qjpeg4.dll"
    Delete "$INSTDIR\qt4_plugins\imageformats\qsvg4.dll"
    Delete "$INSTDIR\qt4_plugins\imageformats\qtga4.dll"
    Delete "$INSTDIR\qt4_plugins\imageformats\qtiff4.dll"
    Delete "$INSTDIR\Include\pyconfig.h"
    Delete "$INSTDIR\_ctypes.pyd"
    Delete "$INSTDIR\_hashlib.pyd"
    Delete "$INSTDIR\_socket.pyd"
    Delete "$INSTDIR\_ssl.pyd"
    Delete "$INSTDIR\bz2.pyd"
    Delete "$INSTDIR\Microsoft.VC90.CRT.manifest"
    Delete "$INSTDIR\msvcm90.dll"
    Delete "$INSTDIR\msvcp90.dll"
    Delete "$INSTDIR\msvcr90.dll"
    Delete "$INSTDIR\onionshare.exe.manifest"
    Delete "$INSTDIR\pyexpat.pyd"
    Delete "$INSTDIR\PyQt4.QtCore.pyd"
    Delete "$INSTDIR\PyQt4.QtGui.pyd"
    Delete "$INSTDIR\python27.dll"
    Delete "$INSTDIR\pywintypes27.dll"
    Delete "$INSTDIR\QtCore4.dll"
    Delete "$INSTDIR\QtGui4.dll"
    Delete "$INSTDIR\QtOpenGL4.dll"
    Delete "$INSTDIR\QtSvg4.dll"
    Delete "$INSTDIR\QtXml4.dll"
    Delete "$INSTDIR\select.pyd"
    Delete "$INSTDIR\sip.pyd"
    Delete "$INSTDIR\unicodedata.pyd"
    Delete "$INSTDIR\win32api.pyd"
    Delete "$INSTDIR\win32pipe.pyd"
    Delete "$INSTDIR\win32wnet.pyd"

    rmDir "$INSTDIR\onionshare"
    rmDir "$INSTDIR\onionshare_gui"
    rmDir "$INSTDIR\images"
    rmDir "$INSTDIR\locale"
    rmDir "$INSTDIR\Include"
    rmDir "$INSTDIR\qt4_plugins\accessible"
    rmDir "$INSTDIR\qt4_plugins\bearer"
    rmDir "$INSTDIR\qt4_plugins\codecs"
    rmDir "$INSTDIR\qt4_plugins\graphicssystems"
    rmDir "$INSTDIR\qt4_plugins\iconengines"
    rmDir "$INSTDIR\qt4_plugins\imageformats"
    rmDir "$INSTDIR\qt4_plugins"
    rmDir "$INSTDIR"

    # remove uninstaller information from the registry
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
SectionEnd
