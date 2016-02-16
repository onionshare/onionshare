!define APPNAME "OnionShare"
!define BINPATH "..\dist"
!define ABOUTURL "https:\\onionshare.org\"

# change these with each release
!define INSTALLSIZE 60104
!define VERSIONMAJOR 0
!define VERSIONMINOR 8
!define VERSIONSTRING "0.8.1"

RequestExecutionLevel admin

Name "OnionShare"
InstallDir "$PROGRAMFILES\${APPNAME}"
LicenseData "license.txt"
Icon "onionshare.ico"

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

# in order to code sign uninstall.exe, we need to do some hacky stuff outlined
# here: http:\\nsis.sourceforge.net\Signing_an_Uninstaller
!ifdef INNER
    !echo "Creating uninstall.exe"
    OutFile "$%TEMP%\tempinstaller.exe"
    SetCompress off
!else
    !echo "Creating normal installer"
    !system "makensis.exe /DINNER onionshare.nsi" = 0
    !system "$%TEMP%\tempinstaller.exe" = 2
    !system "signtool.exe sign /v /d $\"Uninstall OnionShare$\" /a /tr http://timestamp.globalsign.com/scripts/timstamp.dll /fd sha256 $%TEMP%\uninstall.exe" = 0

    # all done, now we can build the real installer
    OutFile "..\dist\OnionShare_Setup.exe"
    SetCompressor /FINAL /SOLID lzma
!endif

Function .onInit
    !ifdef INNER
        WriteUninstaller "$%TEMP%\uninstall.exe"
        Quit # bail out early
    !endif

    setShellVarContext all
    !insertmacro VerifyUserIsAdmin
FunctionEnd

Section "install"
    # application
    SetOutPath "$INSTDIR"
    File "${BINPATH}\onionshare.exe"
    File "${BINPATH}\license.txt"
    File "${BINPATH}\version"
    File "${BINPATH}\onionshare.ico"
    SetOutPath "$INSTDIR\html"
    File "${BINPATH}\html\404.html"
    File "${BINPATH}\html\index.html"
    SetOutPath "$INSTDIR\images"
    File "${BINPATH}\images\logo.png"
    File "${BINPATH}\images\drop_files.png"
    File "${BINPATH}\images\server_stopped.png"
    File "${BINPATH}\images\server_started.png"
    File "${BINPATH}\images\server_working.png"
    SetOutPath "$INSTDIR\locale"
    File "${BINPATH}\locale\de.json"
    File "${BINPATH}\locale\en.json"
    File "${BINPATH}\locale\eo.json"
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
    SetOutPath "$INSTDIR\platforms"
    File "${BINPATH}\platforms\qwindows.dll"
    SetOutPath $INSTDIR
    File "${BINPATH}\_bz2.pyd"
    File "${BINPATH}\_ctypes.pyd"
    File "${BINPATH}\_decimal.pyd"
    File "${BINPATH}\_hashlib.pyd"
    File "${BINPATH}\_lzma.pyd"
    File "${BINPATH}\_multiprocessing.pyd"
    File "${BINPATH}\_socket.pyd"
    File "${BINPATH}\_ssl.pyd"
    File "${BINPATH}\icudt53.dll"
    File "${BINPATH}\icuin53.dll"
    File "${BINPATH}\icuuc53.dll"
    File "${BINPATH}\library.zip"
    File "${BINPATH}\license.txt"
    File "${BINPATH}\pyexpat.pyd"
    File "${BINPATH}\PyQt5.QtCore.pyd"
    File "${BINPATH}\PyQt5.QtGui.pyd"
    File "${BINPATH}\PyQt5.QtWidgets.pyd"
    File "${BINPATH}\python34.dll"
    File "${BINPATH}\pywintypes34.dll"
    File "${BINPATH}\Qt5Core.dll"
    File "${BINPATH}\Qt5Gui.dll"
    File "${BINPATH}\Qt5Widgets.dll"
    File "${BINPATH}\select.pyd"
    File "${BINPATH}\sip.pyd"
    File "${BINPATH}\unicodedata.pyd"
    File "${BINPATH}\win32wnet.pyd"

    # uninstaller
    !ifndef INNER
        SetOutPath $INSTDIR
        File $%TEMP%\uninstall.exe
    !endif

    # start menu
    CreateShortCut "$SMPROGRAMS\${APPNAME}.lnk" "$INSTDIR\onionshare.exe" "" "$INSTDIR\onionshare.ico"

    # registry information for add\remove programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "QuietUninstallString" "$\"$INSTDIR\uninstall.exe$\" \S"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "InstallLocation" "$\"$INSTDIR$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayIcon" "$\"$INSTDIR\onionshare.ico$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLInfoAbout" "$\"${ABOUTURL}$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayVersion" ${VERSIONSTRING}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "VersionMajor" ${VERSIONMAJOR}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "VersionMinor" ${VERSIONMINOR}
    # there is no option for modifying or repairing the install
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoRepair" 1
    # set the INSTALLSIZE constant (!defined at the top of this script) so Add\Remove Programs can accurately report the size
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

!ifdef INNER
    Section "uninstall"
        Delete "$SMPROGRAMS\${APPNAME}.lnk"

        # remove files
        Delete "$INSTDIR\onionshare.exe"
        Delete "$INSTDIR\license.txt"
        Delete "$INSTDIR\version"
        Delete "$INSTDIR\onionshare.ico"
        Delete "$INSTDIR\html\404.html"
        Delete "$INSTDIR\html\index.html"
        Delete "$INSTDIR\images\logo.png"
        Delete "$INSTDIR\images\drop_files.png"
        Delete "$INSTDIR\images\server_stopped.png"
        Delete "$INSTDIR\images\server_started.png"
        Delete "$INSTDIR\images\server_working.png"
        Delete "$INSTDIR\locale\de.json"
        Delete "$INSTDIR\locale\en.json"
        Delete "$INSTDIR\locale\eo.json"
        Delete "$INSTDIR\locale\es.json"
        Delete "$INSTDIR\locale\fi.json"
        Delete "$INSTDIR\locale\fr.json"
        Delete "$INSTDIR\locale\it.json"
        Delete "$INSTDIR\locale\nl.json"
        Delete "$INSTDIR\locale\no.json"
        Delete "$INSTDIR\locale\pt.json"
        Delete "$INSTDIR\locale\ru.json"
        Delete "$INSTDIR\locale\tr.json"
        Delete "$INSTDIR\platforms\qwindows.dll"
        Delete "$INSTDIR\_bz2.pyd"
        Delete "$INSTDIR\_ctypes.pyd"
        Delete "$INSTDIR\_decimal.pyd"
        Delete "$INSTDIR\_hashlib.pyd"
        Delete "$INSTDIR\_lzma.pyd"
        Delete "$INSTDIR\_multiprocessing.pyd"
        Delete "$INSTDIR\_socket.pyd"
        Delete "$INSTDIR\_ssl.pyd"
        Delete "$INSTDIR\icudt53.dll"
        Delete "$INSTDIR\icuin53.dll"
        Delete "$INSTDIR\icuuc53.dll"
        Delete "$INSTDIR\library.zip"
        Delete "$INSTDIR\license.txt"
        Delete "$INSTDIR\pyexpat.pyd"
        Delete "$INSTDIR\PyQt5.QtCore.pyd"
        Delete "$INSTDIR\PyQt5.QtGui.pyd"
        Delete "$INSTDIR\PyQt5.QtWidgets.pyd"
        Delete "$INSTDIR\python34.dll"
        Delete "$INSTDIR\pywintypes34.dll"
        Delete "$INSTDIR\Qt5Core.dll"
        Delete "$INSTDIR\Qt5Gui.dll"
        Delete "$INSTDIR\Qt5Widgets.dll"
        Delete "$INSTDIR\select.pyd"
        Delete "$INSTDIR\sip.pyd"
        Delete "$INSTDIR\unicodedata.pyd"
        Delete "$INSTDIR\win32wnet.pyd"

        Delete "$INSTDIR\uninstall.exe"

        rmDir "$INSTDIR\html"
        rmDir "$INSTDIR\images"
        rmDir "$INSTDIR\locale"
        rmDir "$INSTDIR\platforms"
        rmDir "$INSTDIR"

        # remove uninstaller information from the registry
        DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
    SectionEnd
!endif
