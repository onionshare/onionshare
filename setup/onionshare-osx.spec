# -*- mode: python -*-
a = Analysis(['setup/onionshare-launcher.py'],
    pathex=['.'],
    hiddenimports=['onionshare', 'onionshare_gui'],
    hookspath=None,
    runtime_hooks=None)
a.datas += [
    ('onionshare/strings.json', 'onionshare/strings.json', 'DATA'),
    ('onionshare/index.html', 'onionshare/index.html', 'DATA'),
    ('onionshare/404.html', 'onionshare/404.html', 'DATA'),
    ('images/logo.png', 'onionshare_gui/images/logo.png', 'DATA'),
    ('images/drop_files.png', 'onionshare_gui/images/drop_files.png', 'DATA'),
    ('images/server_stopped.png', 'onionshare_gui/images/server_stopped.png', 'DATA'),
    ('images/server_started.png', 'onionshare_gui/images/server_started.png', 'DATA'),
    ('images/server_working.png', 'onionshare_gui/images/server_working.png', 'DATA'),
]
pyz = PYZ(a.pure)
exe = EXE(pyz,
    a.scripts,
    exclude_binaries=True,
    name='onionshare-launcher',
    debug=False,
    strip=False,
    upx=True,
    console=False )
coll = COLLECT(exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='onionshare')
app = BUNDLE(exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='OnionShare.app',
    appname='OnionShare',
    icon='setup/onionshare.icns',
    version=open('version').read().strip())
