#!/usr/bin/env python3
from distutils.command.build import build
import sys
import os
import inspect
import click
import shutil
import subprocess
import uuid
import xml.etree.ElementTree as ET

root = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    )
)
desktop_dir = os.path.join(root, "desktop")


def get_build_path():
    if "64 bit" in sys.version:
        python_arch = "win-amd64"
    else:
        python_arch = "win32"
    return os.path.join(desktop_dir, "build", f"exe.{python_arch}-3.9")


def get_size(dir):
    size = 0
    for path, dirs, files in os.walk(dir):
        for f in files:
            fp = os.path.join(path, f)
            size += os.path.getsize(fp)
    return size


def run(cmd, cwd=None, error_ok=False):
    print(cmd)
    try:
        subprocess.run(cmd, cwd=cwd, check=True)
    except subprocess.CalledProcessError as e:
        if not error_ok:
            raise subprocess.CalledProcessError(e)


def sign(filename):
    click.echo(f"> Signing {filename}")
    run(
        [
            shutil.which("signtool"),
            "sign",
            "/v",
            "/d",
            "OnionShare",
            "/sha1",
            "1a0345732140749bdaa03efe8591b2c2a036884c",
            "/fd",
            "SHA256",
            "/td",
            "SHA256",
            "/tr",
            "http://timestamp.digicert.com",
            filename,
        ]
    )


def wix_build_data(dirname, dir_prefix, id_, name):
    data = {
        "id": id_,
        "name": name,
        "files": [],
        "dirs": [],
    }

    for basename in os.listdir(dirname):
        filename = os.path.join(dirname, basename)
        if os.path.isfile(filename):
            data["files"].append(os.path.join(dir_prefix, basename))
        elif os.path.isdir(filename):
            if id_ == "INSTALLDIR":
                id_prefix = "Folder"
            else:
                id_prefix = id_

            # Skip lib/Pyside2/Examples folder
            if "\\lib\\PySide2\\examples" in dirname:
                continue

            id_value = f"{id_prefix}{basename.capitalize().replace('-', '_')}"
            data["dirs"].append(
                wix_build_data(
                    os.path.join(dirname, basename),
                    os.path.join(dir_prefix, basename),
                    id_value,
                    basename,
                )
            )

    if len(data["files"]) > 0:
        if id_ == "INSTALLDIR":
            data["component_id"] = "ApplicationFiles"
        else:
            data["component_id"] = "FolderComponent" + id_[len("Folder") :]
        data["component_guid"] = str(uuid.uuid4())

    return data


def wix_build_dir_xml(root, data):
    attrs = {}
    if "id" in data:
        attrs["Id"] = data["id"]
    if "name" in data:
        attrs["Name"] = data["name"]
    el = ET.SubElement(root, "Directory", attrs)
    for subdata in data["dirs"]:
        wix_build_dir_xml(el, subdata)

    # If this is the ProgramMenuFolder, add the menu component
    if "id" in data and data["id"] == "ProgramMenuFolder":
        component_el = ET.SubElement(
            el,
            "Component",
            Id="ApplicationShortcuts",
            Guid="539e7de8-a124-4c09-aa55-0dd516aad7bc",
        )
        ET.SubElement(
            component_el,
            "Shortcut",
            Id="ApplicationShortcut1",
            Name="OnionShare",
            Description="OnionShare",
            Target="[INSTALLDIR]onionshare.exe",
            WorkingDirectory="INSTALLDIR",
        )
        ET.SubElement(
            component_el,
            "RegistryValue",
            Root="HKCU",
            Key="Software\OnionShare",
            Name="installed",
            Type="integer",
            Value="1",
            KeyPath="yes",
        )


def wix_build_components_xml(root, data):
    component_ids = []
    if "component_id" in data:
        component_ids.append(data["component_id"])

    for subdata in data["dirs"]:
        if "component_guid" in subdata:
            dir_ref_el = ET.SubElement(root, "DirectoryRef", Id=subdata["id"])
            component_el = ET.SubElement(
                dir_ref_el,
                "Component",
                Id=subdata["component_id"],
                Guid=subdata["component_guid"],
            )
            for filename in subdata["files"]:
                file_el = ET.SubElement(
                    component_el, "File", Source=filename, Id="file_" + uuid.uuid4().hex
                )

        component_ids += wix_build_components_xml(root, subdata)

    return component_ids


def msi_package(build_path, msi_path, product_update_code):
    print(f"> Build the WiX file")
    version_filename = os.path.join(
        build_path, "lib", "onionshare_cli", "resources", "version.txt"
    )
    with open(version_filename) as f:
        version = f.read().strip()
        # change a version like 2.6.dev1 to just 2.6, for cx_Freeze's sake
        last_digit = version[-1]
        if version.endswith(f".dev{last_digit}"):
            version = version[0:-5]

    data = {
        "id": "TARGETDIR",
        "name": "SourceDir",
        "dirs": [
            {
                "id": "ProgramFilesFolder",
                "dirs": [],
            },
            {
                "id": "ProgramMenuFolder",
                "dirs": [],
            },
        ],
    }

    data["dirs"][0]["dirs"].append(
        wix_build_data(
            build_path,
            ".",
            "INSTALLDIR",
            "OnionShare",
        )
    )

    root_el = ET.Element("Wix", xmlns="http://schemas.microsoft.com/wix/2006/wi")
    product_el = ET.SubElement(
        root_el,
        "Product",
        Name="OnionShare",
        Manufacturer="Micah Lee, et al.",
        Id="*",
        UpgradeCode="$(var.ProductUpgradeCode)",
        Language="1033",
        Codepage="1252",
        Version="$(var.ProductVersion)",
    )
    ET.SubElement(
        product_el,
        "Package",
        Id="*",
        Keywords="Installer",
        Description="OnionShare $(var.ProductVersion) Installer",
        Manufacturer="Micah Lee, et al.",
        InstallerVersion="100",
        Languages="1033",
        Compressed="yes",
        SummaryCodepage="1252",
    )
    ET.SubElement(product_el, "Media", Id="1", Cabinet="product.cab", EmbedCab="yes")
    ET.SubElement(
        product_el,
        "Icon",
        Id="ProductIcon",
        SourceFile=os.path.join(
            desktop_dir, "onionshare", "resources", "onionshare.ico"
        ),
    )
    ET.SubElement(product_el, "Property", Id="ARPPRODUCTICON", Value="ProductIcon")
    ET.SubElement(
        product_el,
        "Property",
        Id="ARPHELPLINK",
        Value="https://docs.onionshare.org",
    )
    ET.SubElement(
        product_el,
        "Property",
        Id="ARPURLINFOABOUT",
        Value="https://onionshare.org",
    )
    ET.SubElement(product_el, "UIRef", Id="WixUI_Minimal")
    ET.SubElement(product_el, "UIRef", Id="WixUI_ErrorProgressText")
    ET.SubElement(
        product_el,
        "WixVariable",
        Id="WixUILicenseRtf",
        Value=os.path.join(desktop_dir, "package", "license.rtf"),
    )
    ET.SubElement(
        product_el,
        "WixVariable",
        Id="WixUIDialogBmp",
        Value=os.path.join(desktop_dir, "package", "dialog.bmp"),
    )
    ET.SubElement(
        product_el,
        "MajorUpgrade",
        AllowSameVersionUpgrades="yes",
        DowngradeErrorMessage="A newer version of [ProductName] is already installed. If you are sure you want to downgrade, remove the existing installation via Programs and Features.",
    )

    wix_build_dir_xml(product_el, data)
    component_ids = wix_build_components_xml(product_el, data)

    feature_el = ET.SubElement(product_el, "Feature", Id="DefaultFeature", Level="1")
    for component_id in component_ids:
        ET.SubElement(feature_el, "ComponentRef", Id=component_id)
    ET.SubElement(feature_el, "ComponentRef", Id="ApplicationShortcuts")

    with open(os.path.join(build_path, "OnionShare.wxs"), "w") as f:
        f.write('<?xml version="1.0" encoding="windows-1252"?>\n')
        f.write(f'<?define ProductVersion = "{version}"?>\n')
        f.write(f'<?define ProductUpgradeCode = "{product_update_code}"?>\n')

        ET.indent(root_el)
        f.write(ET.tostring(root_el).decode())

    print(f"> Build the MSI")
    run(
        [shutil.which("candle.exe"), "OnionShare.wxs"],
        build_path,
    )
    run(
        [shutil.which("light.exe"), "-ext", "WixUIExtension", "OnionShare.wixobj"],
        build_path,
    )

    print(f"> Prepare OnionShare.msi for signing")
    run(
        [
            shutil.which("insignia.exe"),
            "-im",
            os.path.join(build_path, "OnionShare.msi"),
        ],
        error_ok=True,
    )
    sign(os.path.join(build_path, "OnionShare.msi"))

    print(f"> Final MSI: {msi_path}")
    os.makedirs(os.path.join(desktop_dir, "dist"), exist_ok=True)
    os.rename(
        os.path.join(build_path, "OnionShare.msi"),
        msi_path,
    )


@click.group()
def main():
    """
    Windows build tasks
    """


@main.command()
def cleanup_build():
    """Delete unused PySide2 stuff to save space"""
    build_path = get_build_path()
    before_size = get_size(build_path)

    for dirname in ["examples", "qml"]:
        shutil.rmtree(os.path.join(build_path, "lib", "PySide2", dirname))
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
                build_path,
                "lib",
                "PySide2",
                filename.replace("/", "\\"),
            )
        )

    after_size = get_size(build_path)
    freed_bytes = before_size - after_size
    freed_mb = int(freed_bytes / 1024 / 1024)
    print(f"Freed {freed_mb} mb")


@main.command()
@click.argument("win32_path")
@click.argument("win64_path")
def codesign(win32_path, win64_path):
    """Sign Windows binaries before packaging"""
    paths = [win32_path, win64_path]

    for path in paths:
        if not os.path.isdir(path):
            click.echo("Invalid build path")
            return

    for path in paths:
        sign(os.path.join(path, "onionshare.exe"))
        sign(os.path.join(path, "onionshare-cli.exe"))
        sign(
            os.path.join(
                path,
                "lib",
                "onionshare",
                "resources",
                "tor",
                "meek-client.exe",
            )
        )
        sign(
            os.path.join(
                path,
                "lib",
                "onionshare",
                "resources",
                "tor",
                "obfs4proxy.exe",
            )
        )
        sign(
            os.path.join(
                path,
                "lib",
                "onionshare",
                "resources",
                "tor",
                "snowflake-client.exe",
            )
        )


@main.command()
@click.argument("win32_path")
@click.argument("win64_path")
def package(win32_path, win64_path):
    """Build the MSI package"""
    version_filename = os.path.join(
        root, "cli", "onionshare_cli", "resources", "version.txt"
    )
    with open(version_filename) as f:
        version = f.read().strip()

    msi_package(
        win32_path,
        os.path.join(desktop_dir, "dist", f"OnionShare-win32-{version}.msi"),
        "12b9695c-965b-4be0-bc33-21274e809576",
    )
    msi_package(
        win64_path,
        os.path.join(desktop_dir, "dist", f"OnionShare-win64-{version}.msi"),
        "ed7f9243-3528-4b4a-b85c-9943982e75eb",
    )


if __name__ == "__main__":
    main()
