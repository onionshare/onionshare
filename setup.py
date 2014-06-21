#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, platform
from glob import glob

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

def file_list(path):
    files = []
    for filename in os.listdir(path):
        if os.path.isfile(path+'/'+filename):
            files.append(path+'/'+filename)
    return files

version = open('version').read().strip()
args = {}

if platform.system() == 'Darwin':
    args['data_files'] = ['LICENSE', 'README.md', 'version']
    args['app'] = ['setup/onionshare-launcher.py']
    args['options'] = {
        'py2app': {
            'argv_emulation': True,
            'packages': ['flask', 'stem', 'jinja2', 'onionshare_gui', 'onionshare'],
            'includes': ['PyQt4'],
            'excludes': ['PyQt4.QtDesigner', 'PyQt4.QtOpenGL', 'PyQt4.QtScript', 'PyQt4.QtSql', 'PyQt4.QtTest', 'PyQt4.QtXml', 'PyQt4.phonon'],
            'iconfile': 'setup/onionshare.icns',
            'site_packages': True,
            'plist': {
                'CFBundleName': 'OnionShare',
            }
        }
    }
    args['setup_requires'] = 'py2app'

elif platform.system() == 'Windows':
    import py2exe
    args['windows'] = [{'script':'setup/onionshare-launcher.py'}]
    args['data_files'] = [
        ('', ['LICENSE', 'README.md', 'version']),
        ('onionshare', ['onionshare/index.html', 'onionshare/404.html', 'onionshare/strings.json']),
        ('onionshare_gui', ['onionshare_gui/onionshare-icon.png']),
        ('onionshare_gui/templates', glob('onionshare_gui/templates/*')),
        ('onionshare_gui/static', glob('onionshare_gui/static/*'))
    ]
    args['options'] = {
        'py2exe': {
            'includes': ['sip', 'PyQt4', 'PyQt4.QtNetwork'],
            'dll_excludes': ['MSVCP90.dll'],
            'packages': ['jinja2', 'flask', 'stem'],
            'skip_archive': True
        }
    }

else:
    args['packages'] = ['onionshare', 'onionshare_gui']
    args['include_package_data'] = True
    args['scripts'] = ['bin/onionshare', 'bin/onionshare-gui']
    args['data_files'] = [
        ('/usr/share/applications', ['setup/onionshare.desktop']),
        ('/usr/share/pixmaps', ['setup/onionshare80.xpm'])
    ]

setup(
    name='onionshare',
    version=version,
    description='OnionShare lets you securely and anonymously share a file of any size with someone. It works by starting a web server, making it accessible as a Tor hidden service, and generating an unguessable URL to access and download the file.',
    long_description="""OnionShare lets you securely and anonymously share a file of any size with someone. It works by starting a web server, making it accessible as a Tor hidden service, and generating an unguessable URL to access and download the file. It doesn't require setting up a server on the internet somewhere or using a third party filesharing service. You host the file on your own computer and use a Tor hidden service to make it temporarily accessible over the internet. The other user just needs to use Tor Browser to download the file from you.""",
    author='Micah Lee',
    author_email='micah@micahflee.com',
    url='https://github.com/micahflee/onionshare',
    license="GPL v3",
    keywords='onion, share, onionshare, tor, anonymous, web server',
    **args
)

