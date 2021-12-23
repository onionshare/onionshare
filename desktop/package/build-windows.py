#!/usr/bin/env python3
import os
import inspect
import subprocess
import shutil


root = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    )
)


def run(cmd, cwd=None):
    print(cmd)
    subprocess.run(cmd, cwd=cwd, check=True)


def get_size(dir):
    size = 0
    for path, dirs, files in os.walk(dir):
        for f in files:
            fp = os.path.join(path, f)
            size += os.path.getsize(fp)
    return size


def main():
    desktop_dir = os.path.join(root, "desktop")

    print("○ Clean up from last build")
    if os.path.exists(os.path.join(desktop_dir, "build")):
        shutil.rmtree(os.path.join(desktop_dir, "build"))

    print("○ Building binaires")
    run(
        [
            shutil.which("python"),
            "setup-freeze.py",
            "build",
        ],
        desktop_dir,
    )
    before_size = get_size(os.path.join(desktop_dir, "build", "exe.win32-3.9"))

    print("○ Delete unused PySide2 stuff to save space")
    for dirname in ["examples", "qml"]:
        shutil.rmtree(
            os.path.join(
                desktop_dir, "build", "exe.win32-3.9", "lib", "PySide2", dirname
            )
        )
    for filename in [
        "lconvert.exe",
        "linguist.exe",
        "lrelease.exe",
        "lupdate.exe",
        "plugins/assetimporters/assimp.dll",
        "plugins/assetimporters/uip.dll",
        "plugins/audio/qtaudio_wasapi.dll",
        "plugins/audio/qtaudio_windows.dll",
        "plugins/bearer/qgenericbearer.dll",
        "plugins/canbus/qtpassthrucanbus.dll",
        "plugins/canbus/qtpeakcanbus.dll",
        "plugins/canbus/qtsysteccanbus.dll",
        "plugins/canbus/qttinycanbus.dll",
        "plugins/canbus/qtvectorcanbus.dll",
        "plugins/canbus/qtvirtualcanbus.dll",
        "plugins/gamepads/xinputgamepad.dll",
        "plugins/generic/qtuiotouchplugin.dll",
        "plugins/geometryloaders/defaultgeometryloader.dll",
        "plugins/geometryloaders/gltfgeometryloader.dll",
        "plugins/geoservices/qtgeoservices_esri.dll",
        "plugins/geoservices/qtgeoservices_itemsoverlay.dll",
        "plugins/geoservices/qtgeoservices_mapbox.dll",
        "plugins/geoservices/qtgeoservices_nokia.dll",
        "plugins/geoservices/qtgeoservices_osm.dll",
        "plugins/mediaservice/dsengine.dll",
        "plugins/mediaservice/qtmedia_audioengine.dll",
        "plugins/mediaservice/wmfengine.dll",
        "plugins/platforminputcontexts/qtvirtualkeyboardplugin.dll",
        "plugins/platforms/qdirect2d.dll",
        "plugins/platforms/qoffscreen.dll",
        "plugins/platforms/qwebgl.dll",
        "plugins/platformthemes/qxdgdesktopportal.dll",
        "plugins/playlistformats/qtmultimedia_m3u.dll",
        "plugins/position/qtposition_positionpoll.dll",
        "plugins/position/qtposition_serialnmea.dll",
        "plugins/position/qtposition_winrt.dll",
        "plugins/printsupport/windowsprintersupport.dll",
        "plugins/qmltooling/qmldbg_debugger.dll",
        "plugins/qmltooling/qmldbg_inspector.dll",
        "plugins/qmltooling/qmldbg_local.dll",
        "plugins/qmltooling/qmldbg_messages.dll",
        "plugins/qmltooling/qmldbg_native.dll",
        "plugins/qmltooling/qmldbg_nativedebugger.dll",
        "plugins/qmltooling/qmldbg_preview.dll",
        "plugins/qmltooling/qmldbg_profiler.dll",
        "plugins/qmltooling/qmldbg_quickprofiler.dll",
        "plugins/qmltooling/qmldbg_server.dll",
        "plugins/qmltooling/qmldbg_tcp.dll",
        "plugins/renderers/openglrenderer.dll",
        "plugins/renderplugins/scene2d.dll",
        "plugins/scenegraph/qsgd3d12backend.dll",
        "plugins/sceneparsers/gltfsceneexport.dll",
        "plugins/sceneparsers/gltfsceneimport.dll",
        "plugins/sensorgestures/qtsensorgestures_plugin.dll",
        "plugins/sensorgestures/qtsensorgestures_shakeplugin.dll",
        "plugins/sensors/qtsensors_generic.dll",
        "plugins/sqldrivers/qsqlite.dll",
        "plugins/sqldrivers/qsqlodbc.dll",
        "plugins/sqldrivers/qsqlpsql.dll",
        "plugins/styles/qwindowsvistastyle.dll",
        "plugins/texttospeech/qtexttospeech_sapi.dll",
        "plugins/virtualkeyboard/qtvirtualkeyboard_hangul.dll",
        "plugins/virtualkeyboard/qtvirtualkeyboard_openwnn.dll",
        "plugins/virtualkeyboard/qtvirtualkeyboard_pinyin.dll",
        "plugins/virtualkeyboard/qtvirtualkeyboard_tcime.dll",
        "plugins/virtualkeyboard/qtvirtualkeyboard_thai.dll",
        "plugins/webview/qtwebview_webengine.dll",
        "pyside2-lupdate.exe",
        "Qt3DAnimation.pyd",
        "Qt3DAnimation.pyi",
        "Qt3DCore.pyd",
        "Qt3DCore.pyi",
        "Qt3DExtras.pyd",
        "Qt3DExtras.pyi",
        "Qt3DInput.pyd",
        "Qt3DInput.pyi",
        "Qt3DLogic.pyd",
        "Qt3DLogic.pyi",
        "Qt3DRender.pyd",
        "Qt3DRender.pyi",
        "Qt53DAnimation.dll",
        "Qt53DCore.dll",
        "Qt53DExtras.dll",
        "Qt53DInput.dll",
        "Qt53DLogic.dll",
        "Qt53DQuick.dll",
        "Qt53DQuickAnimation.dll",
        "Qt53DQuickExtras.dll",
        "Qt53DQuickInput.dll",
        "Qt53DQuickRender.dll",
        "Qt53DQuickScene2D.dll",
        "Qt53DRender.dll",
        "Qt5Bluetooth.dll",
        "Qt5Bodymovin.dll",
        "Qt5Charts.dll",
        "Qt5Concurrent.dll",
        "Qt5DataVisualization.dll",
        "Qt5DBus.dll",
        "Qt5Designer.dll",
        "Qt5DesignerComponents.dll",
        "Qt5Gamepad.dll",
        "Qt5Help.dll",
        "Qt5Location.dll",
        "Qt5Multimedia.dll",
        "Qt5MultimediaQuick.dll",
        "Qt5MultimediaWidgets.dll",
        "Qt5Nfc.dll",
        "Qt5OpenGL.dll",
        "Qt5Pdf.dll",
        "Qt5PdfWidgets.dll",
        "Qt5Positioning.dll",
        "Qt5PositioningQuick.dll",
        "Qt5PrintSupport.dll",
        "Qt5Purchasing.dll",
        "Qt5Quick.dll",
        "Qt5Quick3D.dll",
        "Qt5Quick3DAssetImport.dll",
        "Qt5Quick3DRender.dll",
        "Qt5Quick3DRuntimeRender.dll",
        "Qt5Quick3DUtils.dll",
        "Qt5QuickControls2.dll",
        "Qt5QuickParticles.dll",
        "Qt5QuickShapes.dll",
        "Qt5QuickTemplates2.dll",
        "Qt5QuickTest.dll",
        "Qt5QuickWidgets.dll",
        "Qt5RemoteObjects.dll",
        "Qt5Script.dll",
        "Qt5ScriptTools.dll",
        "Qt5Scxml.dll",
        "Qt5Sensors.dll",
        "Qt5SerialBus.dll",
        "Qt5SerialPort.dll",
        "Qt5Sql.dll",
        "Qt5Svg.dll",
        "Qt5Test.dll",
        "Qt5TextToSpeech.dll",
        "Qt5VirtualKeyboard.dll",
        "Qt5WebChannel.dll",
        "Qt5WebEngine.dll",
        "Qt5WebEngineCore.dll",
        "Qt5WebEngineWidgets.dll",
        "Qt5WebSockets.dll",
        "Qt5WebView.dll",
        "Qt5Xml.dll",
        "Qt5XmlPatterns.dll",
        "QtAxContainer.pyd",
        "QtAxContainer.pyi",
        "QtCharts.pyd",
        "QtCharts.pyi",
        "QtConcurrent.pyd",
        "QtConcurrent.pyi",
        "QtDataVisualization.pyd",
        "QtDataVisualization.pyi",
        "qtdiag.exe",
        "QtHelp.pyd",
        "QtHelp.pyi",
        "QtLocation.pyd",
        "QtLocation.pyi",
        "QtMultimedia.pyd",
        "QtMultimedia.pyi",
        "QtMultimediaWidgets.pyd",
        "QtMultimediaWidgets.pyi",
        "QtNetwork.pyd",
        "QtNetwork.pyi",
        "QtOpenGL.pyd",
        "QtOpenGL.pyi",
        "QtOpenGLFunctions.pyd",
        "QtOpenGLFunctions.pyi",
        "QtPositioning.pyd",
        "QtPositioning.pyi",
        "QtPrintSupport.pyd",
        "QtPrintSupport.pyi",
        "QtQml.pyd",
        "QtQml.pyi",
        "QtQuick.pyd",
        "QtQuick.pyi",
        "QtQuickControls2.pyd",
        "QtQuickControls2.pyi",
        "QtQuickWidgets.pyd",
        "QtQuickWidgets.pyi",
        "QtRemoteObjects.pyd",
        "QtRemoteObjects.pyi",
        "QtScript.pyd",
        "QtScript.pyi",
        "QtScriptTools.pyd",
        "QtScriptTools.pyi",
        "QtScxml.pyd",
        "QtScxml.pyi",
        "QtSensors.pyd",
        "QtSensors.pyi",
        "QtSerialPort.pyd",
        "QtSerialPort.pyi",
        "QtSql.pyd",
        "QtSql.pyi",
        "QtSvg.pyd",
        "QtSvg.pyi",
        "QtTest.pyd",
        "QtTest.pyi",
        "QtTextToSpeech.pyd",
        "QtTextToSpeech.pyi",
        "QtUiTools.pyd",
        "QtUiTools.pyi",
        "QtWebChannel.pyd",
        "QtWebChannel.pyi",
        "QtWebEngine.pyd",
        "QtWebEngine.pyi",
        "QtWebEngineCore.pyd",
        "QtWebEngineCore.pyi",
        "QtWebEngineProcess.exe",
        "QtWebEngineWidgets.pyd",
        "QtWebEngineWidgets.pyi",
        "QtWebSockets.pyd",
        "QtWebSockets.pyi",
        "QtWinExtras.pyd",
        "QtWinExtras.pyi",
        "QtXml.pyd",
        "QtXml.pyi",
        "QtXmlPatterns.pyd",
        "QtXmlPatterns.pyi",
        "rcc.exe",
        "uic.exe",
    ]:
        os.remove(
            os.path.join(
                desktop_dir,
                "build",
                "exe.win32-3.9",
                "lib",
                "PySide2",
                filename.replace("/", "\\"),
            )
        )

    after_size = get_size(os.path.join(desktop_dir, "build", "exe.win32-3.9"))
    freed_bytes = before_size - after_size
    freed_mb = freed_bytes / 1024 / 1024
    print(f"○ Freed {freed_mb} mb")


if __name__ == "__main__":
    main()
