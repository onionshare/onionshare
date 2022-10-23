#!/usr/bin/env python3
import os
import inspect
import click
import subprocess
import shutil
import glob
import itertools

root = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    )
)
desktop_dir = os.path.join(root, "desktop")

identity_name_application = "Developer ID Application: Micah Lee (N9B95FDWH4)"
entitlements_plist_path = f"{desktop_dir}/package/Entitlements.plist"


def get_app_path():
    return os.path.join(desktop_dir, "build", "OnionShare.app")


def run(cmd, cwd=None, error_ok=False):
    print(f"{cmd} # cwd={cwd}")
    subprocess.run(cmd, cwd=cwd, check=True)


def get_size(dir):
    size = 0
    for path, dirs, files in os.walk(dir):
        for f in files:
            fp = os.path.join(path, f)
            size += os.path.getsize(fp)
    return size


def sign(path, entitlements, identity):
    run(
        [
            "codesign",
            "--sign",
            identity,
            "--entitlements",
            str(entitlements),
            "--timestamp",
            "--deep",
            "--force",
            "--options",
            "runtime,library",
            str(path),
        ]
    )


@click.group()
def main():
    """
    macOS build tasks
    """


@main.command()
def cleanup_build():
    """Delete unused PySide6 stuff to save space"""
    app_path = get_app_path()
    before_size = get_size(app_path)

    print("> Delete unused Qt Frameworks")
    for framework in [
        "QtMultimediaQuick",
        "QtQuickControls2",
        "QtQuickParticles",
        "QtRemoteObjects",
        "Qt3DInput",
        "QtNetworkAuth",
        "QtDataVisualization",
        "QtWebEngineCore",
        "Qt3DQuickRender",
        "Qt3DQuickExtras",
        "QtDesigner",
        "QtNfc",
        "QtQuick3DAssetImport",
        "QtWebEngineWidgets",
        "QtQuickWidgets",
        "Qt3DQuickInput",
        "Qt3DQuickScene2D",
        "Qt3DRender",
        "QtQuick3DRuntimeRender",
        "QtHelp",
        "QtPrintSupport",
        "QtCharts",
        "QtWebSockets",
        "QtQuick3DUtils",
        "QtQuickTemplates2",
        "QtPositioningQuick",
        "Qt3DCore",
        "QtXml",
        "QtSerialPort",
        "QtQuick",
        "QtScxml",
        "QtQml",
        "Qt3DExtras",
        "QtWebChannel",
        "QtMultimedia",
        "QtQmlWorkerScript",
        "QtVirtualKeyboard",
        "QtOpenGL",
        "Qt3DQuick",
        "QtTest",
        "QtPositioning",
        "QtBluetooth",
        "QtQuick3D",
        "Qt3DLogic",
        "QtQuickShapes",
        "QtQuickTest",
        "QtNetwork",
        "QtSvg",
        "QtDesignerComponents",
        "QtMultimediaWidgets",
        "QtQmlModels",
        "Qt3DQuickAnimation",
        "QtSensors",
        "Qt3DAnimation",
        "QtSql",
        "QtConcurrent",
        "QtChartsQml",
        "QtDataVisualizationQml",
        "QtLabsAnimation",
        "QtLabsFolderListModel",
        "QtLabsQmlModels",
        "QtLabsSettings",
        "QtLabsSharedImage",
        "QtLabsWavefrontMesh",
        "QtOpenGLWidgets",
        "QtQmlCore",
        "QtQmlLocalStorage",
        "QtQmlXmlListModel",
        "QtQuick3DAssetUtils",
        "QtQuick3DEffects",
        "QtQuick3DGlslParser",
        "QtQuick3DHelpers",
        "QtQuick3DIblBaker",
        "QtQuick3DParticleEffects",
        "QtQuick3DParticles",
        "QtQuickControls2Impl",
        "QtQuickDialogs2",
        "QtQuickDialogs2QuickImpl",
        "QtQuickDialogs2Utils",
        "QtQuickLayouts",
        "QtQuickTimeline",
        "QtRemoteObjectsQml",
        "QtScxmlQml",
        "QtSensorsQuick",
        "QtShaderTools",
        "QtStateMachine",
        "QtStateMachineQml",
        "QtSvgWidgets",
        "QtUiTools",
        "QtWebEngineQuick",
        "QtWebEngineQuickDelegatesQml"
    ]:
        shutil.rmtree(
            f"{app_path}/Contents/MacOS/lib/PySide6/Qt/lib/{framework}.framework"
        )
        print(
            f"Deleted: {app_path}/Contents/MacOS/lib/PySide6/Qt/lib/{framework}.framework"
        )
        try:
            os.remove(f"{app_path}/Contents/MacOS/lib/PySide6/{framework}.abi3.so")
            print(f"Deleted: {app_path}/Contents/MacOS/lib/PySide6/{framework}.abi3.so")
        except FileNotFoundError:
            pass
        try:
            os.remove(f"{app_path}/Contents/MacOS/lib/PySide6/{framework}.pyi")
            print(f"Deleted: {app_path}/Contents/MacOS/lib/PySide6/{framework}.pyi")
        except FileNotFoundError:
            pass

    print("> Move files around so Apple will notarize")
    # https://github.com/marcelotduarte/cx_Freeze/issues/594
    # https://gist.github.com/TechnicalPirate/259a9c24878fcad948452cb148af2a2c#file-custom_bdist_mac-py-L415

    # Move lib from MacOS into Resources
    os.rename(
        f"{app_path}/Contents/MacOS/lib",
        f"{app_path}/Contents/Resources/lib",
    )
    run(
        ["ln", "-s", "../Resources/lib"],
        cwd=f"{app_path}/Contents/MacOS",
    )

    # Move frameworks from Resources/lib into Frameworks
    os.makedirs(f"{app_path}/Contents/Frameworks", exist_ok=True)
    for framework_filename in glob.glob(
        f"{app_path}/Contents/Resources/lib/PySide6/Qt/lib/Qt*.framework"
    ):
        basename = os.path.basename(framework_filename)

        os.rename(framework_filename, f"{app_path}/Contents/Frameworks/{basename}")
        run(
            ["ln", "-s", f"../../../../../Frameworks/{basename}"],
            cwd=f"{app_path}/Contents/Resources/lib/PySide6/Qt/lib",
        )
        if os.path.exists(f"{app_path}/Contents/Frameworks/{basename}/Resources"):
            if not os.path.exists(f"{app_path}/Contents/Frameworks/{basename}/Versions/A/Resources"):
                os.rename(
                    f"{app_path}/Contents/Frameworks/{basename}/Resources",
                    f"{app_path}/Contents/Frameworks/{basename}/Versions/A/Resources",
                )
            else:
                shutil.rmtree(f"{app_path}/Contents/Frameworks/{basename}/Resources")
            run(
                ["ln", "-s", "Versions/A/Resources"],
                cwd=f"{app_path}/Contents/Frameworks/{basename}",
            )

        try:
            run(
                ["ln", "-s", "A", "Current"],
                cwd=f"{app_path}/Contents/Frameworks/{basename}/Versions",
            )
        except:
            pass

    # Move Qt plugins
    os.rename(
        f"{app_path}/Contents/Resources/lib/PySide6/Qt/plugins",
        f"{app_path}/Contents/Frameworks/plugins",
    )
    run(
        ["ln", "-s", "../../../../Frameworks/plugins"],
        cwd=f"{app_path}/Contents/Resources/lib/PySide6/Qt",
    )

    print("> Delete more unused PySide6 stuff to save space")
    for filename in [
        f"{app_path}/Contents/Resources/lib/PySide6/Designer.app",
        f"{app_path}/Contents/Resources/lib/PySide6/examples",
        f"{app_path}/Contents/Resources/lib/PySide6/glue",
        f"{app_path}/Contents/Resources/lib/PySide6/include",
        f"{app_path}/Contents/Resources/lib/PySide6/lupdate",
        f"{app_path}/Contents/Resources/lib/PySide6/libpyside6.abi3.6.4.dylib",
        f"{app_path}/Contents/Resources/lib/PySide6/Qt/qml",
        f"{app_path}/Contents/Resources/lib/shiboken6/libshiboken6.abi3.6.4.dylib",
        f"{app_path}/Contents/Resources/lib/PySide6/Assistant.app",
        f"{app_path}/Contents/Resources/lib/PySide6/Linguist.app",
        f"{app_path}/Contents/Resources/lib/PySide6/libpyside6qml.abi3.6.4.dylib",
        f"{app_path}/Contents/Resources/lib/PySide6/lrelease",
        f"{app_path}/Contents/Resources/lib/PySide6/qmlformat",
        f"{app_path}/Contents/Resources/lib/PySide6/qmllint",
        f"{app_path}/Contents/Resources/lib/PySide6/qmlls",
        f"{app_path}/Contents/MacOS/QtBluetooth",
        f"{app_path}/Contents/MacOS/QtConcurrent",
        f"{app_path}/Contents/MacOS/QtDesigner",
        f"{app_path}/Contents/MacOS/QtNetworkAuth",
        f"{app_path}/Contents/MacOS/QtNfc",
        f"{app_path}/Contents/MacOS/QtOpenGL",
        f"{app_path}/Contents/MacOS/QtOpenGLWidgets",
        f"{app_path}/Contents/MacOS/QtPositioning",
        f"{app_path}/Contents/MacOS/QtQuick3D",
        f"{app_path}/Contents/MacOS/QtQuick3DRuntimeRender",
        f"{app_path}/Contents/MacOS/QtQuick3DUtils",
        f"{app_path}/Contents/MacOS/QtShaderTools",
        f"{app_path}/Contents/MacOS/QtStateMachine",
        f"{app_path}/Contents/MacOS/QtSvgWidgets",
        f"{app_path}/Contents/MacOS/QtWebChannel",
        f"{app_path}/Contents/MacOS/QtWebEngineCore",
        f"{app_path}/Contents/MacOS/QtWebEngineQuick",
        f"{app_path}/Contents/MacOS/QtXml",
    ]:
        if os.path.isfile(filename) or os.path.islink(filename):
            os.remove(filename)
            print(f"Deleted: {filename}")
        elif os.path.isdir(filename):
            shutil.rmtree(filename)
            print(f"Deleted: {filename}")
        else:
            print(f"Cannot delete, filename not found: {filename}")

    after_size = get_size(f"{app_path}")
    freed_bytes = before_size - after_size
    freed_mb = int(freed_bytes / 1024 / 1024)
    print(f"> Freed {freed_mb} mb")


@main.command()
@click.argument("app_path")
def codesign(app_path):
    """Sign macOS binaries before packaging"""
    for path in itertools.chain(
        glob.glob(f"{app_path}/Contents/Resources/lib/**/*.so", recursive=True),
        glob.glob(f"{app_path}/Contents/Resources/lib/**/*.dylib", recursive=True),
        [
            f"{app_path}/Contents/Frameworks/QtCore.framework/Versions/A/QtCore",
            f"{app_path}/Contents/Frameworks/QtDBus.framework/Versions/A/QtDBus",
            f"{app_path}/Contents/Frameworks/QtGui.framework/Versions/A/QtGui",
            f"{app_path}/Contents/Frameworks/QtWidgets.framework/Versions/A/QtWidgets",
            f"{app_path}/Contents/Resources/lib/Python",
            f"{app_path}/Contents/Resources/lib/onionshare/resources/tor/meek-client",
            f"{app_path}/Contents/Resources/lib/onionshare/resources/tor/obfs4proxy",
            f"{app_path}/Contents/Resources/lib/onionshare/resources/tor/snowflake-client",
            f"{app_path}/Contents/Resources/lib/onionshare/resources/tor/tor",
            f"{app_path}/Contents/Resources/lib/onionshare/resources/tor/libevent-2.1.7.dylib",
            f"{app_path}/Contents/MacOS/onionshare",
            f"{app_path}/Contents/MacOS/onionshare-cli",
            f"{app_path}",
        ],
    ):
        sign(path, entitlements_plist_path, identity_name_application)

    print(f"> Signed app bundle: {app_path}")


@main.command()
@click.argument("app_path")
def package(app_path):
    """Build the DMG package"""
    if not os.path.exists("/usr/local/bin/create-dmg"):
        print("> Error: create-dmg is not installed")
        return

    print("> Create DMG")
    version_filename = f"{root}/cli/onionshare_cli/resources/version.txt"
    with open(version_filename) as f:
        version = f.read().strip()

    os.makedirs(f"{desktop_dir}/dist", exist_ok=True)
    dmg_path = f"{desktop_dir}/dist/OnionShare-{version}.dmg"
    run(
        [
            "create-dmg",
            "--volname",
            "OnionShare",
            "--volicon",
            f"{desktop_dir}/onionshare/resources/onionshare.icns",
            "--window-size",
            "400",
            "200",
            "--icon-size",
            "100",
            "--icon",
            "OnionShare.app",
            "100",
            "70",
            "--hide-extension",
            "OnionShare.app",
            "--app-drop-link",
            "300",
            "70",
            dmg_path,
            app_path,
            "--identity",
            identity_name_application,
        ]
    )

    print(f"> Finished building DMG: {dmg_path}")


if __name__ == "__main__":
    main()
