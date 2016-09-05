!define APPNAME "OnionShare"
!define BINPATH "..\build\exe.win32-3.5"
!define ABOUTURL "https:\\onionshare.org\"

# change these with each release
!define INSTALLSIZE 35630
!define VERSIONMAJOR 0
!define VERSIONMINOR 9
!define VERSIONSTRING "0.9.1"

RequestExecutionLevel admin

Name "OnionShare"
InstallDir "$PROGRAMFILES\${APPNAME}"
LicenseData "..\resources\license.txt"
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
    SetOutPath "$INSTDIR"
    File "onionshare.ico"
    SetOutPath "$INSTDIR\imageformats"
    File "${BINPATH}\imageformats\qdds.dll"
    File "${BINPATH}\imageformats\qgif.dll"
    File "${BINPATH}\imageformats\qicns.dll"
    File "${BINPATH}\imageformats\qico.dll"
    File "${BINPATH}\imageformats\qjpeg.dll"
    File "${BINPATH}\imageformats\qsvg.dll"
    File "${BINPATH}\imageformats\qtga.dll"
    File "${BINPATH}\imageformats\qtiff.dll"
    File "${BINPATH}\imageformats\qwbmp.dll"
    File "${BINPATH}\imageformats\qwebp.dll"
    SetOutPath "$INSTDIR\platforms"
    File "${BINPATH}\platforms\qminimal.dll"
    File "${BINPATH}\platforms\qoffscreen.dll"
    File "${BINPATH}\platforms\qwindows.dll"
    SetOutPath "$INSTDIR\resources"
    File "${BINPATH}\resources\license.txt"
    File "${BINPATH}\resources\version.txt"
    File "${BINPATH}\resources\wordlist.txt"
    SetOutPath "$INSTDIR\resources\html"
    File "${BINPATH}\resources\html\404.html"
    File "${BINPATH}\resources\html\denied.html"
    File "${BINPATH}\resources\html\index.html"
    SetOutPath "$INSTDIR\resources\images"
    File "${BINPATH}\resources\images\logo.png"
    File "${BINPATH}\resources\images\drop_files.png"
    File "${BINPATH}\resources\images\server_stopped.png"
    File "${BINPATH}\resources\images\server_started.png"
    File "${BINPATH}\resources\images\server_working.png"
    SetOutPath "$INSTDIR\resources\locale"
    File "${BINPATH}\resources\locale\de.json"
    File "${BINPATH}\resources\locale\en.json"
    File "${BINPATH}\resources\locale\eo.json"
    File "${BINPATH}\resources\locale\es.json"
    File "${BINPATH}\resources\locale\fi.json"
    File "${BINPATH}\resources\locale\fr.json"
    File "${BINPATH}\resources\locale\it.json"
    File "${BINPATH}\resources\locale\nl.json"
    File "${BINPATH}\resources\locale\no.json"
    File "${BINPATH}\resources\locale\pt.json"
    File "${BINPATH}\resources\locale\ru.json"
    File "${BINPATH}\resources\locale\tr.json"
    SetOutPath "$INSTDIR"
    File "${BINPATH}\MSVCP140.dll"
    File "${BINPATH}\onionshare-gui.exe"
    File "${BINPATH}\onionshare.exe"
    File "${BINPATH}\pyexpat.pyd"
    File "${BINPATH}\PyQt5.QtCore.pyd"
    File "${BINPATH}\PyQt5.QtGui.pyd"
    File "${BINPATH}\PyQt5.QtWidgets.pyd"
    File "${BINPATH}\python35.dll"
    File "${BINPATH}\python35.zip"
    File "${BINPATH}\pywintypes35.dll"
    File "${BINPATH}\Qt5Core.dll"
    File "${BINPATH}\Qt5Gui.dll"
    File "${BINPATH}\Qt5Svg.dll"
    File "${BINPATH}\Qt5Widgets.dll"
    File "${BINPATH}\select.pyd"
    File "${BINPATH}\sip.pyd"
    File "${BINPATH}\unicodedata.pyd"
    File "${BINPATH}\VCRUNTIME140.dll"
    File "${BINPATH}\win32wnet.pyd"
    File "${BINPATH}\_bz2.pyd"
    File "${BINPATH}\_ctypes.pyd"
    File "${BINPATH}\_decimal.pyd"
    File "${BINPATH}\_hashlib.pyd"
    File "${BINPATH}\_lzma.pyd"
    File "${BINPATH}\_multiprocessing.pyd"
    File "${BINPATH}\_socket.pyd"
    File "${BINPATH}\_ssl.pyd"

    # uninstaller
    !ifndef INNER
        SetOutPath $INSTDIR
        File $%TEMP%\uninstall.exe
    !endif

    # start menu
    CreateShortCut "$SMPROGRAMS\${APPNAME}.lnk" "$INSTDIR\onionshare-gui.exe" "" "$INSTDIR\onionshare.ico"

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
        Delete "$INSTDIR\imageformats\qdds.dll"
        Delete "$INSTDIR\imageformats\qgif.dll"
        Delete "$INSTDIR\imageformats\qicns.dll"
        Delete "$INSTDIR\imageformats\qico.dll"
        Delete "$INSTDIR\imageformats\qjpeg.dll"
        Delete "$INSTDIR\imageformats\qsvg.dll"
        Delete "$INSTDIR\imageformats\qtga.dll"
        Delete "$INSTDIR\imageformats\qtiff.dll"
        Delete "$INSTDIR\imageformats\qwbmp.dll"
        Delete "$INSTDIR\imageformats\qwebp.dll"
        Delete "$INSTDIR\platforms\qminimal.dll"
        Delete "$INSTDIR\platforms\qoffscreen.dll"
        Delete "$INSTDIR\platforms\qwindows.dll"
        Delete "$INSTDIR\resources\license.txt"
        Delete "$INSTDIR\resources\version.txt"
        Delete "$INSTDIR\resources\wordlist.txt"
        Delete "$INSTDIR\resources\html\404.html"
        Delete "$INSTDIR\resources\html\denied.html"
        Delete "$INSTDIR\resources\html\index.html"
        Delete "$INSTDIR\resources\images\logo.png"
        Delete "$INSTDIR\resources\images\drop_files.png"
        Delete "$INSTDIR\resources\images\server_stopped.png"
        Delete "$INSTDIR\resources\images\server_started.png"
        Delete "$INSTDIR\resources\images\server_working.png"
        Delete "$INSTDIR\resources\locale\de.json"
        Delete "$INSTDIR\resources\locale\en.json"
        Delete "$INSTDIR\resources\locale\eo.json"
        Delete "$INSTDIR\resources\locale\es.json"
        Delete "$INSTDIR\resources\locale\fi.json"
        Delete "$INSTDIR\resources\locale\fr.json"
        Delete "$INSTDIR\resources\locale\it.json"
        Delete "$INSTDIR\resources\locale\nl.json"
        Delete "$INSTDIR\resources\locale\no.json"
        Delete "$INSTDIR\resources\locale\pt.json"
        Delete "$INSTDIR\resources\locale\ru.json"
        Delete "$INSTDIR\resources\locale\tr.json"
        Delete "$INSTDIR\MSVCP140.dll"
        Delete "$INSTDIR\onionshare-gui.exe"
        Delete "$INSTDIR\onionshare.exe"
        Delete "$INSTDIR\pyexpat.pyd"
        Delete "$INSTDIR\PyQt5.QtCore.pyd"
        Delete "$INSTDIR\PyQt5.QtGui.pyd"
        Delete "$INSTDIR\PyQt5.QtWidgets.pyd"
        Delete "$INSTDIR\python35.dll"
        Delete "$INSTDIR\python35.zip"
        Delete "$INSTDIR\pywintypes35.dll"
        Delete "$INSTDIR\Qt5Core.dll"
        Delete "$INSTDIR\Qt5Gui.dll"
        Delete "$INSTDIR\Qt5Svg.dll"
        Delete "$INSTDIR\Qt5Widgets.dll"
        Delete "$INSTDIR\select.pyd"
        Delete "$INSTDIR\sip.pyd"
        Delete "$INSTDIR\unicodedata.pyd"
        Delete "$INSTDIR\VCRUNTIME140.dll"
        Delete "$INSTDIR\win32wnet.pyd"
        Delete "$INSTDIR\_bz2.pyd"
        Delete "$INSTDIR\_ctypes.pyd"
        Delete "$INSTDIR\_decimal.pyd"
        Delete "$INSTDIR\_hashlib.pyd"
        Delete "$INSTDIR\_lzma.pyd"
        Delete "$INSTDIR\_multiprocessing.pyd"
        Delete "$INSTDIR\_socket.pyd"
        Delete "$INSTDIR\_ssl.pyd"

        Delete "$INSTDIR\onionshare.ico"
        Delete "$INSTDIR\uninstall.exe"

        rmDir "$INSTDIR\imageformats"
        rmDir "$INSTDIR\platforms"
        rmDir "$INSTDIR\resources\html"
        rmDir "$INSTDIR\resources\images"
        rmDir "$INSTDIR\resources\locale"
        rmDir "$INSTDIR\resources"
        rmDir "$INSTDIR"

        # remove uninstaller information from the registry
        DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
    SectionEnd
!endif
