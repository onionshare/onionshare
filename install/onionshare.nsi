!define APPNAME "OnionShare"
!define BINPATH "..\dist\onionshare"
!define ABOUTURL "https:\\onionshare.org\"

# change these with each release
!define INSTALLSIZE 54112
!define VERSIONMAJOR 1
!define VERSIONMINOR 1
!define VERSIONSTRING "1.1"

RequestExecutionLevel admin

Name "OnionShare"
InstallDir "$PROGRAMFILES\${APPNAME}"
Icon "onionshare.ico"

!include LogicLib.nsh

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
    OutFile "..\dist\onionshare-setup.exe"
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
    File "${BINPATH}\api-ms-win-core-console-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-datetime-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-debug-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-errorhandling-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-file-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-file-l1-2-0.dll"
    File "${BINPATH}\api-ms-win-core-file-l2-1-0.dll"
    File "${BINPATH}\api-ms-win-core-handle-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-heap-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-interlocked-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-libraryloader-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-localization-l1-2-0.dll"
    File "${BINPATH}\api-ms-win-core-memory-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-namedpipe-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-processenvironment-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-processthreads-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-processthreads-l1-1-1.dll"
    File "${BINPATH}\api-ms-win-core-profile-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-rtlsupport-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-string-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-synch-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-synch-l1-2-0.dll"
    File "${BINPATH}\api-ms-win-core-sysinfo-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-timezone-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-util-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-crt-conio-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-crt-convert-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-crt-environment-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-crt-filesystem-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-crt-heap-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-crt-locale-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-crt-math-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-crt-multibyte-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-crt-process-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-crt-runtime-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-crt-stdio-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-crt-string-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-crt-time-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-crt-utility-l1-1-0.dll"
    File "${BINPATH}\base_library.zip"
    File "${BINPATH}\MSVCP140.dll"
    File "${BINPATH}\MSVCR100.dll"
    File "${BINPATH}\onionshare-gui.exe"
    File "${BINPATH}\onionshare-gui.exe.manifest"
    File "${BINPATH}\pyexpat.pyd"
    File "${BINPATH}\PyQt5.Qt.pyd"
    File "${BINPATH}\PyQt5.QtCore.pyd"
    File "${BINPATH}\PyQt5.QtGui.pyd"
    File "${BINPATH}\PyQt5.QtPrintSupport.pyd"
    File "${BINPATH}\PyQt5.QtWidgets.pyd"
    File "${BINPATH}\python3.dll"
    File "${BINPATH}\python35.dll"
    File "${BINPATH}\pywintypes35.dll"
    File "${BINPATH}\Qt5Core.dll"
    File "${BINPATH}\Qt5Gui.dll"
    File "${BINPATH}\Qt5PrintSupport.dll"
    File "${BINPATH}\Qt5Svg.dll"
    File "${BINPATH}\Qt5Widgets.dll"
    File "${BINPATH}\select.pyd"
    File "${BINPATH}\sip.pyd"
    File "${BINPATH}\ucrtbase.dll"
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

    SetOutPath "$INSTDIR\Include"
    File "${BINPATH}\Include\pyconfig.h"

    SetOutPath "$INSTDIR\lib2to3"
    File "${BINPATH}\lib2to3\Grammar.txt"
    File "${BINPATH}\lib2to3\Grammar3.5.2.final.0.pickle"
    File "${BINPATH}\lib2to3\PatternGrammar.txt"
    File "${BINPATH}\lib2to3\PatternGrammar3.5.2.final.0.pickle"

    SetOutPath "$INSTDIR\share"
    File "${BINPATH}\share\license.txt"
    File "${BINPATH}\share\version.txt"
    File "${BINPATH}\share\wordlist.txt"
    File "${BINPATH}\share\torrc_template-windows"

    SetOutPath "$INSTDIR\share\html"
    File "${BINPATH}\share\html\404.html"
    File "${BINPATH}\share\html\denied.html"
    File "${BINPATH}\share\html\index.html"

    SetOutPath "$INSTDIR\share\images"
    File "${BINPATH}\share\images\drop_files.png"
    File "${BINPATH}\share\images\logo.png"
    File "${BINPATH}\share\images\server_started.png"
    File "${BINPATH}\share\images\server_stopped.png"
    File "${BINPATH}\share\images\server_working.png"
    File "${BINPATH}\share\images\settings.png"

    SetOutPath "$INSTDIR\share\locale"
    File "${BINPATH}\share\locale\cs.json"
    File "${BINPATH}\share\locale\de.json"
    File "${BINPATH}\share\locale\en.json"
    File "${BINPATH}\share\locale\eo.json"
    File "${BINPATH}\share\locale\es.json"
    File "${BINPATH}\share\locale\fi.json"
    File "${BINPATH}\share\locale\fr.json"
    File "${BINPATH}\share\locale\it.json"
    File "${BINPATH}\share\locale\nl.json"
    File "${BINPATH}\share\locale\no.json"
    File "${BINPATH}\share\locale\pt.json"
    File "${BINPATH}\share\locale\ru.json"
    File "${BINPATH}\share\locale\tr.json"

    SetOutPath "$INSTDIR\qt5_plugins\iconengines"
    File "${BINPATH}\qt5_plugins\iconengines\qsvgicon.dll"

    SetOutPath "$INSTDIR\qt5_plugins\imageformats"
    File "${BINPATH}\qt5_plugins\imageformats\qgif.dll"
    File "${BINPATH}\qt5_plugins\imageformats\qicns.dll"
    File "${BINPATH}\qt5_plugins\imageformats\qico.dll"
    File "${BINPATH}\qt5_plugins\imageformats\qjpeg.dll"
    File "${BINPATH}\qt5_plugins\imageformats\qsvg.dll"
    File "${BINPATH}\qt5_plugins\imageformats\qtga.dll"
    File "${BINPATH}\qt5_plugins\imageformats\qtiff.dll"
    File "${BINPATH}\qt5_plugins\imageformats\qwbmp.dll"
    File "${BINPATH}\qt5_plugins\imageformats\qwebp.dll"

    SetOutPath "$INSTDIR\qt5_plugins\platforms"
    File "${BINPATH}\qt5_plugins\platforms\qminimal.dll"
    File "${BINPATH}\qt5_plugins\platforms\qoffscreen.dll"
    File "${BINPATH}\qt5_plugins\platforms\qwindows.dll"

    SetOutPath "$INSTDIR\qt5_plugins\printsupport"
    File "${BINPATH}\qt5_plugins\printsupport\windowsprintersupport.dll"

    SetOutPath "$INSTDIR\tor\Data\Tor"
    File "${BINPATH}\tor\Data\Tor\geoip"
    File "${BINPATH}\tor\Data\Tor\geoip6"

    SetOutPath "$INSTDIR\tor\Tor"
    File "${BINPATH}\tor\Tor\libeay32.dll"
    File "${BINPATH}\tor\Tor\libevent_core-2-0-5.dll"
    File "${BINPATH}\tor\Tor\libevent_extra-2-0-5.dll"
    File "${BINPATH}\tor\Tor\libevent-2-0-5.dll"
    File "${BINPATH}\tor\Tor\libgcc_s_sjlj-1.dll"
    File "${BINPATH}\tor\Tor\libssp-0.dll"
    File "${BINPATH}\tor\Tor\ssleay32.dll"
    File "${BINPATH}\tor\Tor\tor.exe"
    File "${BINPATH}\tor\Tor\zlib1.dll"

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
        Delete "$INSTDIR\api-ms-win-core-console-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-datetime-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-debug-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-errorhandling-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-file-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-file-l1-2-0.dll"
        Delete "$INSTDIR\api-ms-win-core-file-l2-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-handle-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-heap-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-interlocked-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-libraryloader-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-localization-l1-2-0.dll"
        Delete "$INSTDIR\api-ms-win-core-memory-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-namedpipe-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-processenvironment-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-processthreads-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-processthreads-l1-1-1.dll"
        Delete "$INSTDIR\api-ms-win-core-profile-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-rtlsupport-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-string-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-synch-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-synch-l1-2-0.dll"
        Delete "$INSTDIR\api-ms-win-core-sysinfo-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-timezone-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-util-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-crt-conio-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-crt-convert-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-crt-environment-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-crt-filesystem-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-crt-heap-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-crt-locale-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-crt-math-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-crt-multibyte-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-crt-process-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-crt-runtime-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-crt-stdio-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-crt-string-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-crt-time-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-crt-utility-l1-1-0.dll"
        Delete "$INSTDIR\base_library.zip"
        Delete "$INSTDIR\MSVCP140.dll"
        Delete "$INSTDIR\MSVCR100.dll"
        Delete "$INSTDIR\onionshare-gui.exe"
        Delete "$INSTDIR\onionshare-gui.exe.manifest"
        Delete "$INSTDIR\pyexpat.pyd"
        Delete "$INSTDIR\PyQt5.Qt.pyd"
        Delete "$INSTDIR\PyQt5.QtCore.pyd"
        Delete "$INSTDIR\PyQt5.QtGui.pyd"
        Delete "$INSTDIR\PyQt5.QtPrintSupport.pyd"
        Delete "$INSTDIR\PyQt5.QtWidgets.pyd"
        Delete "$INSTDIR\python3.dll"
        Delete "$INSTDIR\python35.dll"
        Delete "$INSTDIR\pywintypes35.dll"
        Delete "$INSTDIR\Qt5Core.dll"
        Delete "$INSTDIR\Qt5Gui.dll"
        Delete "$INSTDIR\Qt5PrintSupport.dll"
        Delete "$INSTDIR\Qt5Svg.dll"
        Delete "$INSTDIR\Qt5Widgets.dll"
        Delete "$INSTDIR\select.pyd"
        Delete "$INSTDIR\sip.pyd"
        Delete "$INSTDIR\ucrtbase.dll"
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
        Delete "$INSTDIR\Include\pyconfig.h"
        Delete "$INSTDIR\lib2to3\Grammar.txt"
        Delete "$INSTDIR\lib2to3\Grammar3.5.2.final.0.pickle"
        Delete "$INSTDIR\lib2to3\PatternGrammar.txt"
        Delete "$INSTDIR\lib2to3\PatternGrammar3.5.2.final.0.pickle"
        Delete "$INSTDIR\share\license.txt"
        Delete "$INSTDIR\share\version.txt"
        Delete "$INSTDIR\share\wordlist.txt"
        Delete "$INSTDIR\share\torrc_template-windows"
        Delete "$INSTDIR\share\html\404.html"
        Delete "$INSTDIR\share\html\denied.html"
        Delete "$INSTDIR\share\html\index.html"
        Delete "$INSTDIR\share\images\drop_files.png"
        Delete "$INSTDIR\share\images\logo.png"
        Delete "$INSTDIR\share\images\server_started.png"
        Delete "$INSTDIR\share\images\server_stopped.png"
        Delete "$INSTDIR\share\images\server_working.png"
        Delete "$INSTDIR\share\images\settings.png"
        Delete "$INSTDIR\share\locale\cs.json"
        Delete "$INSTDIR\share\locale\de.json"
        Delete "$INSTDIR\share\locale\en.json"
        Delete "$INSTDIR\share\locale\eo.json"
        Delete "$INSTDIR\share\locale\es.json"
        Delete "$INSTDIR\share\locale\fi.json"
        Delete "$INSTDIR\share\locale\fr.json"
        Delete "$INSTDIR\share\locale\it.json"
        Delete "$INSTDIR\share\locale\nl.json"
        Delete "$INSTDIR\share\locale\no.json"
        Delete "$INSTDIR\share\locale\pt.json"
        Delete "$INSTDIR\share\locale\ru.json"
        Delete "$INSTDIR\share\locale\tr.json"
        Delete "$INSTDIR\qt5_plugins\iconengines\qsvgicon.dll"
        Delete "$INSTDIR\qt5_plugins\imageformats\qgif.dll"
        Delete "$INSTDIR\qt5_plugins\imageformats\qicns.dll"
        Delete "$INSTDIR\qt5_plugins\imageformats\qico.dll"
        Delete "$INSTDIR\qt5_plugins\imageformats\qjpeg.dll"
        Delete "$INSTDIR\qt5_plugins\imageformats\qsvg.dll"
        Delete "$INSTDIR\qt5_plugins\imageformats\qtga.dll"
        Delete "$INSTDIR\qt5_plugins\imageformats\qtiff.dll"
        Delete "$INSTDIR\qt5_plugins\imageformats\qwbmp.dll"
        Delete "$INSTDIR\qt5_plugins\imageformats\qwebp.dll"
        Delete "$INSTDIR\qt5_plugins\platforms\qminimal.dll"
        Delete "$INSTDIR\qt5_plugins\platforms\qoffscreen.dll"
        Delete "$INSTDIR\qt5_plugins\platforms\qwindows.dll"
        Delete "$INSTDIR\qt5_plugins\printsupport\windowsprintersupport.dll"
        Delete "$INSTDIR\tor\Data\Tor\geoip"
        Delete "$INSTDIR\tor\Data\Tor\geoip6"
        Delete "$INSTDIR\tor\Tor\libeay32.dll"
        Delete "$INSTDIR\tor\Tor\libevent_core-2-0-5.dll"
        Delete "$INSTDIR\tor\Tor\libevent_extra-2-0-5.dll"
        Delete "$INSTDIR\tor\Tor\libevent-2-0-5.dll"
        Delete "$INSTDIR\tor\Tor\libgcc_s_sjlj-1.dll"
        Delete "$INSTDIR\tor\Tor\libssp-0.dll"
        Delete "$INSTDIR\tor\Tor\ssleay32.dll"
        Delete "$INSTDIR\tor\Tor\tor.exe"
        Delete "$INSTDIR\tor\Tor\zlib1.dll"

        Delete "$INSTDIR\onionshare.ico"
        Delete "$INSTDIR\uninstall.exe"

        rmDir "$INSTDIR\Include"
        rmDir "$INSTDIR\lib2to3"
        rmDir "$INSTDIR\share\html"
        rmDir "$INSTDIR\share\images"
        rmDir "$INSTDIR\share\locale"
        rmDir "$INSTDIR\share"
        rmDir "$INSTDIR\qt5_plugins\iconengines"
        rmDir "$INSTDIR\qt5_plugins\imageformats"
        rmDir "$INSTDIR\qt5_plugins\platforms"
        rmDir "$INSTDIR\qt5_plugins\printsupport"
        rmDir "$INSTDIR\qt5_plugins"
        rmDir "$INSTDIR\tor\Data\Tor"
        rmDir "$INSTDIR\tor\Data"
        rmDir "$INSTDIR\tor\Tor"
        rmDir "$INSTDIR\tor"
        rmDir "$INSTDIR"

        # remove uninstaller information from the registry
        DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
    SectionEnd
!endif
