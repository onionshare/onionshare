# -*- mode: python -*-

import platform
system = platform.system()

block_cipher = None

a = Analysis(
    ['linux_scripts/onionshare-gui'],
    pathex=['.'],
    binaries=None,
    datas=[
        ('../images/*', 'images'),
        ('../locale/*', 'locale'),
        ('../onionshare/*.html', 'html'),
        ('../version.txt', '.')
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher)

pyz = PYZ(
    a.pure, a.zipped_data,
    cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name='onionshare',
    debug=False,
    strip=False,
    upx=True,
    console=True)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='onionshare')

if system == 'Darwin':
    app = BUNDLE(
        coll,
        name='OnionShare.app',
        icon='install/onionshare.icns',
        bundle_identifier='com.micahflee.onionshare',
        info_plist={
            'NSHighResolutionCapable': 'True'
        }
    )
