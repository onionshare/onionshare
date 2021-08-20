#!/usr/bin/env python3
import os
import inspect
import subprocess
import argparse
import shutil
import glob
import itertools

root = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        )
    )
)


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
            "runtime",
        ]
    )


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def main():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--with-codesign",
        action="store_true",
        dest="with_codesign",
        help="Codesign the app bundle",
    )
    args = parser.parse_args()

    cli_dir = os.path.join(root, "cli")
    desktop_dir = os.path.join(root, "desktop")

    print("○ Clean up from last build")
    if os.path.exists(os.path.join(cli_dir, "dist")):
        shutil.rmtree(os.path.join(cli_dir, "dist"))
    if os.path.exists(os.path.join(desktop_dir, "macOS")):
        shutil.rmtree(os.path.join(desktop_dir, "macOS"))

    print("○ Build onionshare-cli")
    run(["poetry", "install"], cli_dir)
    run(["poetry", "build"], cli_dir)
    whl_filename = glob.glob(os.path.join(cli_dir, "dist", "*.whl"))[0]
    whl_basename = os.path.basename(whl_filename)
    shutil.copyfile(whl_filename, os.path.join(desktop_dir, whl_basename))

    print("○ Create app bundle")
    run(["briefcase", "create"], desktop_dir)
    app_path = os.path.join(desktop_dir, "macOS", "app", "OnionShare", "OnionShare.app")

    print("○ Delete unused Qt5 frameworks from app bundle")
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
                app_path,
                "Contents",
                "Resources",
                "app_packages",
                "PySide2",
                "Qt",
                "lib",
                f"{framework}.framework",
            )
        )
        try:
            os.remove(
                os.path.join(
                    app_path,
                    "Contents",
                    "Resources",
                    "app_packages",
                    "PySide2",
                    f"{framework}.abi3.so",
                )
            )
            os.remove(
                os.path.join(
                    app_path,
                    "Contents",
                    "Resources",
                    "app_packages",
                    "PySide2",
                    f"{framework}.pyi",
                )
            )
        except FileNotFoundError:
            pass
    shutil.rmtree(
        os.path.join(
            app_path,
            "Contents",
            "Resources",
            "app_packages",
            "PySide2",
            "Designer.app",
        )
    )

    print(f"○ Unsigned app bundle: {app_path}")

    if args.with_codesign:
        identity_name_application = "Developer ID Application: Micah Lee (N9B95FDWH4)"
        entitlements_plist_path = os.path.join(
            desktop_dir, "package", "macos", "Entitlements.plist"
        )

        print("○ Code sign app bundle")
        for path in itertools.chain(
            glob.glob(
                f"{app_path}/Contents/Resources/app_packages/**/*.dylib", recursive=True
            ),
            glob.glob(
                f"{app_path}/Contents/Resources/app_packages/**/*.so", recursive=True
            ),
            glob.glob(
                f"{app_path}/Contents/Resources/Support/**/*.dylib", recursive=True
            ),
            glob.glob(f"{app_path}/Contents/Resources/Support/**/*.so", recursive=True),
            glob.glob(
                f"{app_path}/Contents/Resources/app_packages/PySide2/Qt/lib/**/Versions/5/*",
                recursive=True,
            ),
            [
                f"{app_path}/Contents/Resources/app_packages/PySide2/pyside2-lupdate",
                f"{app_path}/Contents/Resources/app_packages/PySide2/rcc",
                f"{app_path}/Contents/Resources/app_packages/PySide2/uic",
                app_path,
            ],
        ):
            codesign(path, entitlements_plist_path, identity_name_application)
        codesign(app_path, entitlements_plist_path, identity_name_application)
        print(f"○ Signed app bundle: {app_path}")

        if not os.path.exists("/usr/local/bin/create-dmg"):
            print("○ Error: create-dmg is not installed")
            return

        print("○ Create DMG")
        dmg_path = os.path.join(desktop_dir, "macOS", "OnionShare.dmg")
        run(
            [
                "create-dmg",
                "--volname",
                "OnionShare",
                "--volicon",
                os.path.join(
                    desktop_dir, "src", "onionshare", "resources", "onionshare.icns"
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
                app_path,
                "--identity",
                identity_name_application,
            ]
        )

        print(f"○ Finished building DMG: {dmg_path}")


if __name__ == "__main__":
    main()
