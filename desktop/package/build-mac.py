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
    print(cmd)
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
            str(path),
            "--force",
            "--options",
            "runtime,library",
        ]
    )


def main():
    desktop_dir = os.path.join(root, "desktop")

    print("○ Clean up from last build")
    if os.path.exists(os.path.join(desktop_dir, "build")):
        shutil.rmtree(os.path.join(desktop_dir, "build"))
    if os.path.exists(os.path.join(desktop_dir, "dist")):
        shutil.rmtree(os.path.join(desktop_dir, "dist"))

    print("○ Building binaries")
    run(
        [
            shutil.which("python"),
            "setup-freeze.py",
            "bdist_mac",
        ],
        desktop_dir,
    )
    before_size = get_size(
        os.path.join(desktop_dir, "build", "OnionShare.app")
    )

    print("○ Delete unused PySide2 stuff to save space")
    for dirname in [
        "PySide2/Designer.app",
        "PySide2/examples",
        "PySide2/glue",
        "PySide2/Qt/qml",
        "shiboken2/files.dir",
    ]:
        shutil.rmtree(
            os.path.join(
                desktop_dir,
                "build",
                "OnionShare.app",
                "Contents",
                "MacOS",
                "lib",
                dirname,
            )
        )
    shutil.rmtree(
        os.path.join(
            desktop_dir,
            "build",
            "OnionShare.app",
            "Contents",
            "MacOS",
            "lib",
            "shiboken2",
            "docs",
        )
    )
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
        "QtNfc",
        "QtOpenGL",
        "QtPdf",
        "QtPdfWidgets",
        "QtPositioning",
        "QtPositioningQuick",
        "QtPurchasing",
        "QtQml",
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
            os.path.join(
                desktop_dir,
                "build",
                "OnionShare.app",
                "Contents",
                "MacOS",
                "lib",
                "PySide2",
                "Qt",
                "lib",
                f"{framework}.framework",
            )
        )
        try:
            os.remove(
                os.path.join(
                    desktop_dir,
                    "build",
                    "OnionShare.app",
                    "Contents",
                    "MacOS",
                    "lib",
                    "PySide2",
                    f"{framework}.abi3.so",
                )
            )
            os.remove(
                os.path.join(
                    desktop_dir,
                    "build",
                    "OnionShare.app",
                    "Contents",
                    "MacOS",
                    "lib",
                    "PySide2",
                    f"{framework}.pyi",
                )
            )
        except FileNotFoundError:
            pass

    after_size = get_size(
        os.path.join(desktop_dir, "build", "OnionShare.app")
    )
    freed_bytes = before_size - after_size
    freed_mb = int(freed_bytes / 1024 / 1024)
    print(f"○ Freed {freed_mb} mb")

    print("○ Sign app bundle")
    identity_name_application = "Developer ID Application: Micah Lee (N9B95FDWH4)"
    entitlements_plist_path = os.path.join(desktop_dir, "package", "Entitlements.plist")

    for path in itertools.chain(
        glob.glob(
            f"{desktop_dir}/build/OnionShare.app/Contents/MacOS/**/*.dylib",
            recursive=True,
        ),
        glob.glob(
            f"{desktop_dir}/build/OnionShare.app/Contents/MacOS/**/*.so", recursive=True
        ),
        [
            f"{desktop_dir}/build/OnionShare.app/Contents/MacOS/lib/PySide2/pyside2-lupdate",
            f"{desktop_dir}/build/OnionShare.app/Contents/MacOS/lib/PySide2/rcc",
            f"{desktop_dir}/build/OnionShare.app/Contents/MacOS/lib/PySide2/uic",
        ],
    ):
        codesign(path, entitlements_plist_path, identity_name_application)
    codesign(
        f"{desktop_dir}/build/OnionShare.app",
        entitlements_plist_path,
        identity_name_application,
    )
    print(f"○ Signed app bundle: {desktop_dir}/build/OnionShare.app")

    if not os.path.exists("/usr/local/bin/create-dmg"):
        print("○ Error: create-dmg is not installed")
        return

    print("○ Create DMG")
    version_filename = os.path.join(
        root, "cli", "onionshare_cli", "resources", "version.txt"
    )
    with open(version_filename) as f:
        version = f.read().strip()
    
    os.makedirs(os.path.join(desktop_dir, "dist"), exist_ok=True)
    dmg_path = os.path.join(desktop_dir, "dist", f"OnionShare-{version}.dmg")
    run(
        [
            "create-dmg",
            "--volname",
            "OnionShare",
            "--volicon",
            os.path.join(
                desktop_dir, "onionshare", "resources", "onionshare.icns"
            ),
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
            f"{desktop_dir}/build/OnionShare.app",
            "--identity",
            identity_name_application,
        ]
    )

    print(f"○ Finished building DMG: {dmg_path}")

if __name__ == "__main__":
    main()
