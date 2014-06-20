#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, platform
from glob import glob

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

version = open('version').read().strip()
args = {}

if platform.system() == 'Darwin':
    args['data_files'] = ['LICENSE', 'README.md', 'BUILD.md', 'version', 'onionshare', 'onionshare_gui']
    args['app'] = ['setup/onionshare_osx.py']
    args['options'] = {
        'py2app': {
            'argv_emulation': True,
            'iconfile': 'setup/onionshare.icns',
            'packages': ['flask', 'stem'],
            'site_packages': True,
            'plist': {
                'CFBundleName': 'OnionShare',
            }
        }
    }

elif platform.system() == 'Windows':
    pass

else:
    args['data_files'] = [
        ('/usr/share/applications', ['setup/onionshare.desktop']),
        ('/usr/share/pixmaps', ['setup/onionshare80.xpm'])
    ]
    args['scripts'] = ['bin/onionshare', 'bin/onionshare-gui']

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
    include_package_data=True,
    install_requires=[
        'flask >= 0.8',
        'stem >= 1.1.0'
    ],
    packages=['onionshare', 'onionshare_gui'],
    **args
)

