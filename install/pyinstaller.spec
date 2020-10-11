# -*- mode: python -*-

import os
import platform
from distutils.sysconfig import get_python_lib

p = platform.system()

version = open("share/version.txt").read().strip()

paths = ["."]
if p == "Windows":
    paths.append(os.path.join(get_python_lib(), "PyQt5", "Qt", "bin"))
    paths.append(
        os.path.join(
            os.path.abspath(os.sep),
            "Program Files (x86)",
            "Windows Kits",
            "10",
            "bin",
            "x86",
        )
    )
    paths.append(
        os.path.join(
            os.path.abspath(os.sep),
            "Program Files (x86)",
            "Windows Kits",
            "10",
            "bin",
            "x64",
        )
    )
    paths.append(
        os.path.join(
            os.path.abspath(os.sep),
            "Program Files (x86)",
            "Windows Kits",
            "10",
            "Redist",
            "ucrt",
            "DLLs",
            "x86",
        )
    )
    paths.append(
        os.path.join(
            os.path.abspath(os.sep),
            "Program Files (x86)",
            "Windows Kits",
            "10",
            "Redist",
            "ucrt",
            "DLLs",
            "x64",
        )
    )

a = Analysis(
    ["scripts/onionshare-pyinstaller"],
    pathex=paths,
    binaries=None,
    datas=[
        ("../share/version.txt", "share"),
        ("../share/wordlist.txt", "share"),
        ("../share/torrc_template", "share"),
        ("../share/torrc_template-obfs4", "share"),
        ("../share/torrc_template-meek_lite_azure", "share"),
        ("../share/images/*", "share/images"),
        ("../share/locale/*", "share/locale"),
        ("../share/static/*", "share/static"),
        ("../share/templates/*", "share/templates"),
        ("../share/static/css/*", "share/static/css"),
        ("../share/static/img/*", "share/static/img"),
        ("../share/static/js/*", "share/static/js"),
        ("../install/licenses/*", "licenses"),
    ],
    hiddenimports=["engineio.async_drivers.threading"],
    hookspath=[],
    runtime_hooks=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Show console in dev releases, don't show console in production releases
console = "dev" in version

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="onionshare-gui",
    debug=False,
    strip=False,
    upx=True,
    console=console,
)

coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=True, name="onionshare"
)

if p == "Darwin":
    app = BUNDLE(
        coll,
        name="OnionShare.app",
        icon="onionshare.icns",
        bundle_identifier="com.micahflee.onionshare",
        info_plist={
            "CFBundleShortVersionString": version,
            "NSHighResolutionCapable": "True",
        },
    )
