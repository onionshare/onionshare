# -*- mode: python -*-
a = Analysis(['setup/onionshare-launcher.py'],
    hiddenimports=['onionshare', 'onionshare_gui'],
    hookspath=None,
    runtime_hooks=None)
a.datas += [
    ('images/logo.png', 'images/logo.png', 'DATA'),
    ('images/drop_files.png', 'images/drop_files.png', 'DATA'),
    ('images/server_stopped.png', 'images/server_stopped.png', 'DATA'),
    ('images/server_started.png', 'images/server_started.png', 'DATA'),
    ('images/server_working.png', 'images/server_working.png', 'DATA'),
]
pyz = PYZ(a.pure)
exe = EXE(pyz,
    a.scripts,
    exclude_binaries=True,
    name='onionshare.exe',
    debug=False,
    strip=False,
    upx=True,
    icon='setup/onionshare.ico',
    console=False )
coll = COLLECT(exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    Tree('onionshare', prefix='onionshare'),
    Tree('onionshare_gui', prefix='onionshare_gui'),
    [('LICENSE', 'LICENSE', 'DATA')],
    strip=False,
    upx=True,
    name='onionshare')
