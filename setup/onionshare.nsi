!define APPNAME "OnionShare"
!define BINPATH "..\dist\onionshare"
!define ABOUTURL "https://github.com/micahflee/onionshare"

# change these with each release
!define INSTALLSIZE 46094
!define VERSIONMAJOR 0
!define VERSIONMINOR 3
!define VERSIONSTRING "0.3dev"

RequestExecutionLevel admin

SetCompressor /FINAL /SOLID lzma
SetCompressorDictSize 64

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
    File "${BINPATH}\onionshare\404.html"
    File "${BINPATH}\onionshare\__init__.py"
    File "${BINPATH}\onionshare\__init__.pyc"
    File "${BINPATH}\onionshare\index.html"
    File "${BINPATH}\onionshare\onionshare.py"
    File "${BINPATH}\onionshare\onionshare.pyc"
    File "${BINPATH}\onionshare\strings.json"
    SetOutPath "$INSTDIR\onionshare_gui"
    File "${BINPATH}\onionshare_gui\onionshare_gui.py"
    File "${BINPATH}\onionshare_gui\onionshare_gui.pyc"
    File "${BINPATH}\onionshare_gui\webapp.py"
    File "${BINPATH}\onionshare_gui\webapp.pyc"
    File "${BINPATH}\onionshare_gui\onionshare-icon.png"
    File "${BINPATH}\onionshare_gui\__init__.py"
    File "${BINPATH}\onionshare_gui\__init__.pyc"
    SetOutPath "$INSTDIR\onionshare_gui\templates"
    File "${BINPATH}\onionshare_gui\templates\index.html"
    SetOutPath "$INSTDIR\onionshare_gui\static"
    File "${BINPATH}\onionshare_gui\static\logo.png"
    File "${BINPATH}\onionshare_gui\static\jquery-1.11.1.min.js"
    File "${BINPATH}\onionshare_gui\static\onionshare.js"
    File "${BINPATH}\onionshare_gui\static\style.css"
    File "${BINPATH}\onionshare_gui\static\loader.gif"
    File "${BINPATH}\onionshare_gui\static\helpers.js"

    # dependencies
    SetOutPath $INSTDIR
    File "${BINPATH}\LIBEAY32.dll"
    File "${BINPATH}\QtOpenGL4.dll"
    File "${BINPATH}\unicodedata.pyd"
    File "${BINPATH}\sip.pyd"
    File "${BINPATH}\pywintypes27.dll"
    File "${BINPATH}\SSLEAY32.dll"
    File "${BINPATH}\msvcr90.dll"
    File "${BINPATH}\QtSvg4.dll"
    File "${BINPATH}\msvcp90.dll"
    File "${BINPATH}\QtCore4.dll"
    File "${BINPATH}\bz2.pyd"
    File "${BINPATH}\PyQt4.QtCore.pyd"
    File "${BINPATH}\PyQt4.QtNetwork.pyd"
    File "${BINPATH}\QtNetwork4.dll"
    File "${BINPATH}\_ctypes.pyd"
    File "${BINPATH}\PyQt4.QtWebKit.pyd"
    File "${BINPATH}\PyQt4.QtGui.pyd"
    File "${BINPATH}\win32wnet.pyd"
    File "${BINPATH}\win32api.pyd"
    File "${BINPATH}\pyexpat.pyd"
    File "${BINPATH}\python27.dll"
    File "${BINPATH}\msvcm90.dll"
    File "${BINPATH}\_hashlib.pyd"
    File "${BINPATH}\win32pipe.pyd"
    File "${BINPATH}\QtWebKit4.dll"
    File "${BINPATH}\onionshare.exe.manifest"
    File "${BINPATH}\select.pyd"
    File "${BINPATH}\Microsoft.VC90.CRT.manifest"
    File "${BINPATH}\QtGui4.dll"
    File "${BINPATH}\_ssl.pyd"
    File "${BINPATH}\_socket.pyd"
    File "${BINPATH}\QtXml4.dll"
    SetOutPath "$INSTDIR\qt4_plugins\accessible"
    File "${BINPATH}\qt4_plugins\accessible\qtaccessiblewidgets4.dll"
    SetOutPath "$INSTDIR\qt4_plugins\graphicssystems"
    File "${BINPATH}\qt4_plugins\graphicssystems\qglgraphicssystem4.dll"
    SetOutPath "$INSTDIR\qt4_plugins\bearer"
    File "${BINPATH}\qt4_plugins\bearer\qnativewifibearer4.dll"
    File "${BINPATH}\qt4_plugins\bearer\qgenericbearer4.dll"
    SetOutPath "$INSTDIR\qt4_plugins\iconengines"
    File "${BINPATH}\qt4_plugins\iconengines\qsvgicon4.dll"
    SetOutPath "$INSTDIR\qt4_plugins\codecs"
    File "${BINPATH}\qt4_plugins\codecs\qjpcodecs4.dll"
    File "${BINPATH}\qt4_plugins\codecs\qkrcodecs4.dll"
    File "${BINPATH}\qt4_plugins\codecs\qtwcodecs4.dll"
    File "${BINPATH}\qt4_plugins\codecs\qcncodecs4.dll"
    SetOutPath "$INSTDIR\qt4_plugins\imageformats"
    File "${BINPATH}\qt4_plugins\imageformats\qmng4.dll"
    File "${BINPATH}\qt4_plugins\imageformats\qico4.dll"
    File "${BINPATH}\qt4_plugins\imageformats\qgif4.dll"
    File "${BINPATH}\qt4_plugins\imageformats\qjpeg4.dll"
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
    Delete "$INSTDIR\onionshare\404.html"
    Delete "$INSTDIR\onionshare\__init__.py"
    Delete "$INSTDIR\onionshare\__init__.pyc"
    Delete "$INSTDIR\onionshare\index.html"
    Delete "$INSTDIR\onionshare\onionshare.py"
    Delete "$INSTDIR\onionshare\onionshare.pyc"
    Delete "$INSTDIR\onionshare\strings.json"
    Delete "$INSTDIR\onionshare_gui\__init__.py"
    Delete "$INSTDIR\onionshare_gui\__init__.pyc"
    Delete "$INSTDIR\onionshare_gui\templates"
    Delete "$INSTDIR\onionshare_gui\templates\index.html"
    Delete "$INSTDIR\onionshare_gui\static"
    Delete "$INSTDIR\onionshare_gui\static\logo.png"
    Delete "$INSTDIR\onionshare_gui\static\jquery-1.11.1.min.js"
    Delete "$INSTDIR\onionshare_gui\static\onionshare.js"
    Delete "$INSTDIR\onionshare_gui\static\style.css"
    Delete "$INSTDIR\onionshare_gui\static\loader.gif"
    Delete "$INSTDIR\onionshare_gui\static\helpers.js"
    Delete "$INSTDIR\onionshare_gui\onionshare_gui.py"
    Delete "$INSTDIR\onionshare_gui\onionshare_gui.pyc"
    Delete "$INSTDIR\onionshare_gui\webapp.py"
    Delete "$INSTDIR\onionshare_gui\webapp.pyc"
    Delete "$INSTDIR\onionshare_gui\onionshare-icon.png"
    Delete "$INSTDIR\qt4_plugins\accessible\qtaccessiblewidgets4.dll"
    Delete "$INSTDIR\qt4_plugins\graphicssystems\qglgraphicssystem4.dll"
    Delete "$INSTDIR\qt4_plugins\bearer\qnativewifibearer4.dll"
    Delete "$INSTDIR\qt4_plugins\bearer\qgenericbearer4.dll"
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
    Delete "$INSTDIR\LIBEAY32.dll"
    Delete "$INSTDIR\QtOpenGL4.dll"
    Delete "$INSTDIR\unicodedata.pyd"
    Delete "$INSTDIR\sip.pyd"
    Delete "$INSTDIR\pywintypes27.dll"
    Delete "$INSTDIR\SSLEAY32.dll"
    Delete "$INSTDIR\msvcr90.dll"
    Delete "$INSTDIR\QtSvg4.dll"
    Delete "$INSTDIR\msvcp90.dll"
    Delete "$INSTDIR\QtCore4.dll"
    Delete "$INSTDIR\bz2.pyd"
    Delete "$INSTDIR\PyQt4.QtCore.pyd"
    Delete "$INSTDIR\PyQt4.QtNetwork.pyd"
    Delete "$INSTDIR\QtNetwork4.dll"
    Delete "$INSTDIR\_ctypes.pyd"
    Delete "$INSTDIR\PyQt4.QtWebKit.pyd"
    Delete "$INSTDIR\PyQt4.QtGui.pyd"
    Delete "$INSTDIR\win32wnet.pyd"
    Delete "$INSTDIR\win32api.pyd"
    Delete "$INSTDIR\pyexpat.pyd"
    Delete "$INSTDIR\python27.dll"
    Delete "$INSTDIR\msvcm90.dll"
    Delete "$INSTDIR\_hashlib.pyd"
    Delete "$INSTDIR\Include\pyconfig.h"
    Delete "$INSTDIR\win32pipe.pyd"
    Delete "$INSTDIR\QtWebKit4.dll"
    Delete "$INSTDIR\onionshare.exe.manifest"
    Delete "$INSTDIR\select.pyd"
    Delete "$INSTDIR\Microsoft.VC90.CRT.manifest"
    Delete "$INSTDIR\QtGui4.dll"
    Delete "$INSTDIR\_ssl.pyd"
    Delete "$INSTDIR\_socket.pyd"
    Delete "$INSTDIR\QtXml4.dll"

	rmDir "$INSTDIR\onionshare"
    rmDir "$INSTDIR\onionshare_gui\templates"
    rmDir "$INSTDIR\onionshare_gui\static"
    rmDir "$INSTDIR\onionshare_gui"
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
