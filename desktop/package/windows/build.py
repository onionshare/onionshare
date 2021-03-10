#!/usr/bin/env python3
import os
import inspect
import subprocess
import shutil
import glob

root = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        )
    )
)


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def main():
    cli_dir = os.path.join(root, "cli")
    desktop_dir = os.path.join(root, "desktop")

    print("○ Clean up from last build")
    if os.path.exists(os.path.join(cli_dir, "dist")):
        shutil.rmtree(os.path.join(cli_dir, "dist"))
    if os.path.exists(os.path.join(desktop_dir, "windows")):
        shutil.rmtree(os.path.join(desktop_dir, "windows"))

    print("○ Building onionshare-cli")
    run(["poetry", "install"], cli_dir)
    run(["poetry", "build"], cli_dir)
    whl_filename = glob.glob(os.path.join(cli_dir, "dist", "*.whl"))[0]
    whl_basename = os.path.basename(whl_filename)
    shutil.copyfile(whl_filename, os.path.join(desktop_dir, whl_basename))

    print("○ Create the binary")
    run(["briefcase", "create"], desktop_dir)

    print("○ Delete unused Qt5 DLLs to save space")
    for filename in [
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
        "plugins/sceneparsers/assimpsceneimport.dll",
        "plugins/sceneparsers/gltfsceneexport.dll",
        "plugins/sceneparsers/gltfsceneimport.dll",
        "plugins/sensorgestures/qtsensorgestures_plugin.dll",
        "plugins/sensorgestures/qtsensorgestures_shakeplugin.dll",
        "plugins/sensors/qtsensors_generic.dll",
        "plugins/sqldrivers/qsqlite.dll",
        "plugins/sqldrivers/qsqlodbc.dll",
        "plugins/sqldrivers/qsqlpsql.dll",
        "plugins/texttospeech/qtexttospeech_sapi.dll",
        "plugins/virtualkeyboard/qtvirtualkeyboard_hangul.dll",
        "plugins/virtualkeyboard/qtvirtualkeyboard_openwnn.dll",
        "plugins/virtualkeyboard/qtvirtualkeyboard_pinyin.dll",
        "plugins/virtualkeyboard/qtvirtualkeyboard_tcime.dll",
        "plugins/virtualkeyboard/qtvirtualkeyboard_thai.dll",
        "plugins/webview/qtwebview_webengine.dll",
        "qml/Qt/labs/animation/labsanimationplugin.dll",
        "qml/Qt/labs/calendar/qtlabscalendarplugin.dll",
        "qml/Qt/labs/folderlistmodel/qmlfolderlistmodelplugin.dll",
        "qml/Qt/labs/location/locationlabsplugin.dll",
        "qml/Qt/labs/lottieqt/lottieqtplugin.dll",
        "qml/Qt/labs/platform/qtlabsplatformplugin.dll",
        "qml/Qt/labs/qmlmodels/labsmodelsplugin.dll",
        "qml/Qt/labs/settings/qmlsettingsplugin.dll",
        "qml/Qt/labs/sharedimage/sharedimageplugin.dll",
        "qml/Qt/labs/wavefrontmesh/qmlwavefrontmeshplugin.dll",
        "qml/Qt3D/Animation/quick3danimationplugin.dll",
        "qml/Qt3D/Core/quick3dcoreplugin.dll",
        "qml/Qt3D/Extras/quick3dextrasplugin.dll",
        "qml/Qt3D/Input/quick3dinputplugin.dll",
        "qml/Qt3D/Logic/quick3dlogicplugin.dll",
        "qml/Qt3D/Render/quick3drenderplugin.dll",
        "qml/QtBluetooth/declarative_bluetooth.dll",
        "qml/QtCharts/qtchartsqml2.dll",
        "qml/QtDataVisualization/datavisualizationqml2.dll",
        "qml/QtGamepad/declarative_gamepad.dll",
        "qml/QtGraphicalEffects/private/qtgraphicaleffectsprivate.dll",
        "qml/QtGraphicalEffects/qtgraphicaleffectsplugin.dll",
        "qml/QtLocation/declarative_location.dll",
        "qml/QtMultimedia/declarative_multimedia.dll",
        "qml/QtNfc/declarative_nfc.dll",
        "qml/QtPositioning/declarative_positioning.dll",
        "qml/QtPurchasing/declarative_purchasing.dll",
        "qml/QtQml/Models.2/modelsplugin.dll",
        "qml/QtQml/qmlplugin.dll",
        "qml/QtQml/RemoteObjects/qtqmlremoteobjects.dll",
        "qml/QtQml/StateMachine/qtqmlstatemachine.dll",
        "qml/QtQml/WorkerScript.2/workerscriptplugin.dll",
        "qml/QtQuick/Controls/qtquickcontrolsplugin.dll",
        "qml/QtQuick/Controls/Styles/Flat/qtquickextrasflatplugin.dll",
        "qml/QtQuick/Controls.2/Fusion/qtquickcontrols2fusionstyleplugin.dll",
        "qml/QtQuick/Controls.2/Imagine/qtquickcontrols2imaginestyleplugin.dll",
        "qml/QtQuick/Controls.2/Material/qtquickcontrols2materialstyleplugin.dll",
        "qml/QtQuick/Controls.2/qtquickcontrols2plugin.dll",
        "qml/QtQuick/Controls.2/Universal/qtquickcontrols2universalstyleplugin.dll",
        "qml/QtQuick/Dialogs/dialogplugin.dll",
        "qml/QtQuick/Dialogs/Private/dialogsprivateplugin.dll",
        "qml/QtQuick/Extras/qtquickextrasplugin.dll",
        "qml/QtQuick/Layouts/qquicklayoutsplugin.dll",
        "qml/QtQuick/LocalStorage/qmllocalstorageplugin.dll",
        "qml/QtQuick/Particles.2/particlesplugin.dll",
        "qml/QtQuick/Pdf/pdfplugin.dll",
        "qml/QtQuick/PrivateWidgets/widgetsplugin.dll",
        "qml/QtQuick/Scene2D/qtquickscene2dplugin.dll",
        "qml/QtQuick/Scene3D/qtquickscene3dplugin.dll",
        "qml/QtQuick/Shapes/qmlshapesplugin.dll",
        "qml/QtQuick/Templates.2/qtquicktemplates2plugin.dll",
        "qml/QtQuick/Timeline/qtquicktimelineplugin.dll",
        "qml/QtQuick/VirtualKeyboard/qtquickvirtualkeyboardplugin.dll",
        "qml/QtQuick/VirtualKeyboard/Settings/qtquickvirtualkeyboardsettingsplugin.dll",
        "qml/QtQuick/VirtualKeyboard/Styles/qtquickvirtualkeyboardstylesplugin.dll",
        "qml/QtQuick/Window.2/windowplugin.dll",
        "qml/QtQuick/XmlListModel/qmlxmllistmodelplugin.dll",
        "qml/QtQuick.2/qtquick2plugin.dll",
        "qml/QtQuick3D/Effects/qtquick3deffectplugin.dll",
        "qml/QtQuick3D/Helpers/qtquick3dhelpersplugin.dll",
        "qml/QtQuick3D/Materials/qtquick3dmaterialplugin.dll",
        "qml/QtQuick3D/qquick3dplugin.dll",
        "qml/QtRemoteObjects/qtremoteobjects.dll",
        "qml/QtScxml/declarative_scxml.dll",
        "qml/QtSensors/declarative_sensors.dll",
        "qml/QtTest/qmltestplugin.dll",
        "qml/QtWebChannel/declarative_webchannel.dll",
        "qml/QtWebEngine/qtwebengineplugin.dll",
        "qml/QtWebSockets/declarative_qmlwebsockets.dll",
        "qml/QtWebView/declarative_webview.dll",
        "Qt5DBus.dll",
        "Qt5PrintSupport.dll",
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
    ]:
        os.remove(
            os.path.join(
                desktop_dir,
                "windows",
                "OnionShare",
                "src",
                "app_packages",
                "PySide2",
                filename.replace("/", "\\"),
            )
        )

    print("○ Create the installer")
    run(["briefcase", "package"], desktop_dir)
    msi_filename = glob.glob(os.path.join(desktop_dir, "windows", "OnionShare-*.msi"))[
        0
    ]
    print(f"○ Created unsigned installer: {msi_filename}")

    print(f"○ Signing installer")
    run(
        [
            "signtool.exe",
            "sign",
            "/v",
            "/d",
            "OnionShare",
            "/a",
            "/tr",
            "http://time.certum.pl/",
            msi_filename,
        ],
        desktop_dir,
    )
    print(f"○ Signed installer: {msi_filename}")


if __name__ == "__main__":
    main()
