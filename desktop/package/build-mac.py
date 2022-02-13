#!/usr/bin/env python3
import os
import inspect
import subprocess
import shutil
import itertools
import glob

root = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    )
)


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


def codesign(path, entitlements, identity):
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


def main():
    desktop_dir = f"{root}/desktop"
    app_dir = f"{desktop_dir}/build/OnionShare.app"

    print("○ Clean up from last build")
    if os.path.exists(f"{desktop_dir}/build"):
        shutil.rmtree(f"{desktop_dir}/build")
    if os.path.exists(f"{desktop_dir}/dist"):
        shutil.rmtree(f"{desktop_dir}/dist")

    print("○ Building binaries")
    run(
        [
            shutil.which("python"),
            "setup-freeze.py",
            "bdist_mac",
        ],
        desktop_dir,
    )
    before_size = get_size(f"{app_dir}")

    print("○ Delete unused Qt Frameworks")
    for framework in [
        "Qt3DAnimation",
        "Qt3DCore",
        "Qt3DExtras",
        "Qt3DInput",
        "Qt3DLogic",
        "Qt3DQuick",
        "Qt3DQuickAnimation",
        "Qt3DQuickExtras",
        "Qt3DQuickInput",
        "Qt3DQuickRender",
        "Qt3DQuickScene2D",
        "Qt3DRender",
        "QtBluetooth",
        "QtBodymovin",
        "QtCharts",
        "QtConcurrent",
        "QtDataVisualization",
        "QtDesigner",
        "QtDesignerComponents",
        "QtGamepad",
        "QtHelp",
        "QtLocation",
        "QtMultimedia",
        "QtMultimediaQuick",
        "QtMultimediaWidgets",
        "QtNetwork",
        "QtNetworkAuth",
        "QtNfc",
        "QtOpenGL",
        "QtPdf",
        "QtPdfWidgets",
        "QtPositioning",
        "QtPositioningQuick",
        "QtPrintSupport",
        "QtPurchasing",
        "QtQml",
        "QtQmlModels",
        "QtQmlWorkerScript",
        "QtQuick",
        "QtQuick3D",
        "QtQuick3DAssetImport",
        "QtQuick3DRender",
        "QtQuick3DRuntimeRender",
        "QtQuick3DUtils",
        "QtQuickControls2",
        "QtQuickParticles",
        "QtQuickShapes",
        "QtQuickTemplates2",
        "QtQuickTest",
        "QtQuickWidgets",
        "QtRemoteObjects",
        "QtRepParser",
        "QtScript",
        "QtScriptTools",
        "QtScxml",
        "QtSensors",
        "QtSerialBus",
        "QtSerialPort",
        "QtSql",
        "QtSvg",
        "QtTest",
        "QtTextToSpeech",
        "QtUiPlugin",
        "QtVirtualKeyboard",
        "QtWebChannel",
        "QtWebEngine",
        "QtWebEngineCore",
        "QtWebEngineWidgets",
        "QtWebSockets",
        "QtWebView",
        "QtXml",
        "QtXmlPatterns",
    ]:
        shutil.rmtree(
            f"{app_dir}/Contents/MacOS/lib/PySide2/Qt/lib/{framework}.framework"
        )
        try:
            os.remove(
                f"{app_dir}/Contents/MacOS/lib/PySide2/{framework}.abi3.so"
            )
            os.remove(
                f"{app_dir}/Contents/MacOS/lib/PySide2/{framework}.pyi"
            )
        except FileNotFoundError:
            pass

    print("○ Move files around so Apple will notarize")
    # https://github.com/marcelotduarte/cx_Freeze/issues/594
    # https://gist.github.com/TechnicalPirate/259a9c24878fcad948452cb148af2a2c#file-custom_bdist_mac-py-L415

    # Move lib from MacOS into Resources
    os.rename(
        f"{app_dir}/Contents/MacOS/lib",
        f"{app_dir}/Contents/Resources/lib",
    )
    run(
        ["ln", "-s", "../Resources/lib"],
        cwd=f"{app_dir}/Contents/MacOS",
    )

    # Move frameworks from Resources/lib into Frameworks
    os.makedirs(f"{app_dir}/Contents/Frameworks", exist_ok=True)
    for framework_filename in glob.glob(
        f"{app_dir}/Contents/Resources/lib/PySide2/Qt/lib/Qt*.framework"
    ):
        basename = os.path.basename(framework_filename)
        
        os.rename(framework_filename, f"{app_dir}/Contents/Frameworks/{basename}")
        run(
            ["ln", "-s", f"../../../../../Frameworks/{basename}"],
            cwd=f"{app_dir}/Contents/Resources/lib/PySide2/Qt/lib",
        )
        if os.path.exists(f"{app_dir}/Contents/Frameworks/{basename}/Resources"):
            os.rename(
                f"{app_dir}/Contents/Frameworks/{basename}/Resources",
                f"{app_dir}/Contents/Frameworks/{basename}/Versions/5/Resources"
            )
            run(
                ["ln", "-s", "Versions/5/Resources"],
                cwd=f"{app_dir}/Contents/Frameworks/{basename}",
            )

        run(
            ["ln", "-s", "5", "Current"],
            cwd=f"{app_dir}/Contents/Frameworks/{basename}/Versions",
        )
    
    # Move Qt plugins
    os.rename(
        f"{app_dir}/Contents/Resources/lib/PySide2/Qt/plugins",
        f"{app_dir}/Contents/Frameworks/plugins",
    )
    run(
        ["ln", "-s", "../../../../Frameworks/plugins"],
        cwd=f"{app_dir}/Contents/Resources/lib/PySide2/Qt",
    )

    print("○ Delete more unused PySide2 stuff to save space")
    for filename in [
        f"{app_dir}/Contents/Resources/lib/PySide2/Designer.app",
        f"{app_dir}/Contents/Resources/lib/PySide2/examples",
        f"{app_dir}/Contents/Resources/lib/PySide2/glue",
        f"{app_dir}/Contents/Resources/lib/PySide2/include",
        f"{app_dir}/Contents/Resources/lib/PySide2/pyside2-lupdate",
        f"{app_dir}/Contents/Resources/lib/PySide2/Qt/qml",
        f"{app_dir}/Contents/Resources/lib/PySide2/libpyside2.abi3.5.15.dylib",
        f"{app_dir}/Contents/Resources/lib/PySide2/Qt/lib/QtRepParser.framework",
        f"{app_dir}/Contents/Resources/lib/PySide2/Qt/lib/QtUiPlugin.framework",
        f"{app_dir}/Contents/Resources/lib/PySide2/Qt/lib/QtWebEngineCore.framework/Helpers",
        f"{app_dir}/Contents/Resources/lib/shiboken2/libshiboken2.abi3.5.15.dylib",
        f"{app_dir}/Contents/Resources/lib/shiboken2/docs",
        f"{app_dir}/Contents/Resources/lib/PySide2/rcc",
        f"{app_dir}/Contents/Resources/lib/PySide2/uic",
    ]:
        if os.path.isdir(filename):
            shutil.rmtree(filename)
        elif os.path.isfile(filename):
            os.remove(filename)
        else:
            print(f"Cannot delete, filename not found: {filename}")

    after_size = get_size(f"{app_dir}")
    freed_bytes = before_size - after_size
    freed_mb = int(freed_bytes / 1024 / 1024)
    print(f"○ Freed {freed_mb} mb")

    print("○ Sign app bundle")
    identity_name_application = "Developer ID Application: Micah Lee (N9B95FDWH4)"
    entitlements_plist_path = f"{desktop_dir}/package/Entitlements.plist"

    for path in itertools.chain(
        glob.glob(f"{app_dir}/Contents/Resources/lib/**/*.so", recursive=True),
        glob.glob(f"{app_dir}/Contents/Resources/lib/**/*.dylib", recursive=True),
        [
            f"{app_dir}/Contents/Frameworks/QtCore.framework/Versions/5/QtCore",
            f"{app_dir}/Contents/Frameworks/QtDBus.framework/Versions/5/QtDBus",
            f"{app_dir}/Contents/Frameworks/QtGui.framework/Versions/5/QtGui",
            f"{app_dir}/Contents/Frameworks/QtMacExtras.framework/Versions/5/QtMacExtras",
            f"{app_dir}/Contents/Frameworks/QtWidgets.framework/Versions/5/QtWidgets",
            f"{app_dir}/Contents/Resources/lib/Python",
            f"{app_dir}/Contents/Resources/lib/onionshare/resources/tor/meek-client",
            f"{app_dir}/Contents/Resources/lib/onionshare/resources/tor/obfs4proxy",
            f"{app_dir}/Contents/Resources/lib/onionshare/resources/tor/snowflake-client",
            f"{app_dir}/Contents/Resources/lib/onionshare/resources/tor/tor",
            f"{app_dir}/Contents/Resources/lib/onionshare/resources/tor/libevent-2.1.7.dylib",
            f"{app_dir}/Contents/MacOS/onionshare",
            f"{app_dir}/Contents/MacOS/onionshare-cli",
            f"{app_dir}",
        ],
    ):
        codesign(path, entitlements_plist_path, identity_name_application)

    print(f"○ Signed app bundle: {app_dir}")

    if not os.path.exists("/usr/local/bin/create-dmg"):
        print("○ Error: create-dmg is not installed")
        return

    print("○ Create DMG")
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
            f"{app_dir}",
            "--identity",
            identity_name_application,
        ]
    )

    print(f"○ Finished building DMG: {dmg_path}")


if __name__ == "__main__":
    main()
