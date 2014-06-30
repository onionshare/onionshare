# -*- mode: python -*-
a = Analysis(['setup/onionshare-launcher.py'],
    hiddenimports=['onionshare', 'onionshare_gui'],
    hookspath=None,
    runtime_hooks=None)
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
